import path from "path";
import { fileURLToPath } from "url";
import { timingSafeEqual } from "crypto";
import "dotenv/config";
import express, { type NextFunction, type Request, type Response } from "express";
import qrcode from "qrcode";
import { generateOtp, storeOtp, verifyOtp } from "./otp-store.js";
import { getQr, getStatus, hasWhatsApp, sendText, startWhatsApp, toJid } from "./whatsapp.js";
import {
  getSessionQr,
  getSessionStatus,
  listGroupParticipants,
  listGroups,
  logoutSession,
  startSession,
} from "./whatsapp-groups.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = process.env.PORT ? Number(process.env.PORT) : 3210;

// A linked WhatsApp session can read and send messages as a real account -
// whoever can call send-otp/verify-otp effectively has that access. This key
// is the only thing standing between "internal API" and "anyone who can
// reach this port can message anyone as your WhatsApp number," so it's
// required outright rather than silently falling back to an open service.
const API_KEY = process.env.API_KEY;
if (!API_KEY) {
  console.error(
    "FATAL: API_KEY env var is not set. Refusing to start - this service\n" +
      "controls a live WhatsApp session and must not run without an access key."
  );
  process.exit(1);
}

function requireApiKey(req: Request, res: Response, next: NextFunction) {
  const provided = req.header("x-api-key") ?? "";
  const expected = API_KEY!;
  const ok =
    provided.length === expected.length &&
    timingSafeEqual(Buffer.from(provided), Buffer.from(expected));
  if (!ok) {
    res.status(401).json({ error: "Invalid or missing API key." });
    return;
  }
  next();
}

await startWhatsApp();

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, "../public")));

app.get("/api/status", (_req, res) => {
  res.json({ status: getStatus() });
});

app.get("/api/qr", async (_req, res) => {
  const qr = getQr();
  if (!qr) {
    res.status(404).json({ error: "No QR code available right now." });
    return;
  }
  const dataUrl = await qrcode.toDataURL(qr);
  res.json({ qr: dataUrl });
});

app.post("/api/send-otp", requireApiKey, async (req, res) => {
  const phone = String(req.body?.phone ?? "").trim();
  if (!phone) {
    res.status(400).json({ error: "phone is required" });
    return;
  }
  if (getStatus() !== "open") {
    res.status(503).json({ error: "WhatsApp isn't connected yet. Scan the QR code first." });
    return;
  }

  const jid = toJid(phone);
  const exists = await hasWhatsApp(jid);
  if (!exists) {
    res.status(404).json({ error: "This number doesn't appear to have WhatsApp." });
    return;
  }

  const code = generateOtp();
  storeOtp(phone, code);
  try {
    await sendText(jid, `Your verification code is: ${code}\nIt expires in 5 minutes.`);
    res.json({ success: true });
  } catch (error) {
    console.error("Failed to send OTP:", error);
    res.status(502).json({ error: "Failed to send the WhatsApp message." });
  }
});

// Sends an arbitrary message from the shared OTP number - used for things
// like "a teacher added you to their class" pings, which should come from
// the platform's own identity, not a teacher's personal WhatsApp (see
// /api/teacher-sessions/* below, which is read-only by design).
app.post("/api/send-message", requireApiKey, async (req, res) => {
  const phone = String(req.body?.phone ?? "").trim();
  const text = String(req.body?.text ?? "").trim();
  if (!phone || !text) {
    res.status(400).json({ error: "phone and text are required" });
    return;
  }
  if (getStatus() !== "open") {
    res.status(503).json({ error: "WhatsApp isn't connected yet. Scan the QR code first." });
    return;
  }

  const jid = toJid(phone);
  const exists = await hasWhatsApp(jid);
  if (!exists) {
    res.status(404).json({ error: "This number doesn't appear to have WhatsApp." });
    return;
  }

  try {
    await sendText(jid, text);
    res.json({ success: true });
  } catch (error) {
    console.error("Failed to send message:", error);
    res.status(502).json({ error: "Failed to send the WhatsApp message." });
  }
});

app.post("/api/verify-otp", requireApiKey, (req, res) => {
  const phone = String(req.body?.phone ?? "").trim();
  const code = String(req.body?.code ?? "").trim();
  if (!phone || !code) {
    res.status(400).json({ error: "phone and code are required" });
    return;
  }
  const result = verifyOtp(phone, code);
  res.json({ valid: result === "valid", reason: result });
});

// Teacher-linked WhatsApp sessions for browsing/importing their own groups.
// Unlike /api/qr above, every one of these requires the API key - there's no
// "admin scans it once at setup" exception here, since these QRs are
// per-teacher and must never be guessable/reachable from the open internet.
app.post("/api/teacher-sessions/:teacherId/start", requireApiKey, async (req, res) => {
  try {
    await startSession(req.params.teacherId);
    res.json({ status: getSessionStatus(req.params.teacherId) });
  } catch (error) {
    console.error("Failed to start teacher session:", error);
    res.status(400).json({ error: "Invalid teacher id." });
  }
});

app.get("/api/teacher-sessions/:teacherId/status", requireApiKey, (req, res) => {
  res.json({ status: getSessionStatus(req.params.teacherId) });
});

app.get("/api/teacher-sessions/:teacherId/qr", requireApiKey, async (req, res) => {
  const qr = getSessionQr(req.params.teacherId);
  if (!qr) {
    res.status(404).json({ error: "No QR code available right now." });
    return;
  }
  const dataUrl = await qrcode.toDataURL(qr);
  res.json({ qr: dataUrl });
});

app.get("/api/teacher-sessions/:teacherId/groups", requireApiKey, async (req, res) => {
  try {
    const groups = await listGroups(req.params.teacherId);
    res.json({ groups });
  } catch (error) {
    console.error("Failed to list groups:", error);
    res.status(409).json({ error: "WhatsApp session is not connected." });
  }
});

app.get("/api/teacher-sessions/:teacherId/groups/:groupId/participants", requireApiKey, async (req, res) => {
  try {
    const phoneNumbers = await listGroupParticipants(req.params.teacherId, req.params.groupId);
    res.json({ phone_numbers: phoneNumbers });
  } catch (error) {
    console.error("Failed to list group participants:", error);
    res.status(409).json({ error: "WhatsApp session is not connected." });
  }
});

// Teacher sessions are read-only by design (browse/sync groups only) - any
// outbound message goes out from the shared OTP number instead, via
// /api/send-message above. This just unlinks the device and wipes its
// stored credentials.
app.post("/api/teacher-sessions/:teacherId/logout", requireApiKey, async (req, res) => {
  try {
    await logoutSession(req.params.teacherId);
    res.json({ success: true });
  } catch (error) {
    console.error("Failed to disconnect teacher session:", error);
    res.status(500).json({ error: "Failed to disconnect the WhatsApp session." });
  }
});

app.listen(PORT, () => {
  console.log(`WhatsApp OTP service listening on http://localhost:${PORT}`);
});
