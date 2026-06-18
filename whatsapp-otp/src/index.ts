import path from "path";
import { fileURLToPath } from "url";
import { timingSafeEqual } from "crypto";
import "dotenv/config";
import express, { type NextFunction, type Request, type Response } from "express";
import qrcode from "qrcode";
import { generateOtp, storeOtp, verifyOtp } from "./otp-store.js";
import { getQr, getStatus, hasWhatsApp, sendText, startWhatsApp, toJid } from "./whatsapp.js";

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

app.listen(PORT, () => {
  console.log(`WhatsApp OTP service listening on http://localhost:${PORT}`);
});
