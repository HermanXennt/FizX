import { rm } from "fs/promises";
import { Boom } from "@hapi/boom";
import makeWASocket, {
  useMultiFileAuthState,
  fetchLatestBaileysVersion,
  DisconnectReason,
  type WASocket,
} from "@whiskeysockets/baileys";
import pino from "pino";

// Separate from whatsapp.ts on purpose - that file owns the single shared
// session used for login OTPs. This one manages one independent session per
// teacher who links their own personal WhatsApp, so a bug here can never
// take down OTP delivery and vice versa.
const AUTH_ROOT = process.env.WA_TEACHER_AUTH_DIR ?? "./auth-teachers";

const logger = pino({ level: "warn" });

export type ConnectionStatus = "disconnected" | "connecting" | "qr" | "open" | "closed";

interface Session {
  sock: WASocket | null;
  status: ConnectionStatus;
  qr: string | null;
}

const sessions = new Map<string, Session>();

// teacherId is a Django UUID, but it crosses a network boundary before it
// ever touches a filesystem path - never trust it blindly.
function sanitizeId(teacherId: string): string {
  if (!/^[a-zA-Z0-9-]+$/.test(teacherId)) {
    throw new Error("Invalid teacher id.");
  }
  return teacherId;
}

function getOrCreateSession(teacherId: string): Session {
  let session = sessions.get(teacherId);
  if (!session) {
    session = { sock: null, status: "disconnected", qr: null };
    sessions.set(teacherId, session);
  }
  return session;
}

export function getSessionStatus(teacherId: string): ConnectionStatus {
  return sessions.get(teacherId)?.status ?? "disconnected";
}

export function getSessionQr(teacherId: string): string | null {
  return sessions.get(teacherId)?.qr ?? null;
}

export async function startSession(rawTeacherId: string): Promise<void> {
  const teacherId = sanitizeId(rawTeacherId);
  const session = getOrCreateSession(teacherId);

  // Already connecting/connected - starting again would orphan the existing
  // socket instead of reusing it.
  if (session.sock && (session.status === "open" || session.status === "connecting" || session.status === "qr")) {
    return;
  }

  const { state, saveCreds } = await useMultiFileAuthState(`${AUTH_ROOT}/${teacherId}`);
  const { version } = await fetchLatestBaileysVersion();

  const sock = makeWASocket({ auth: state, logger, version });
  session.sock = sock;
  session.status = "connecting";

  sock.ev.on("creds.update", saveCreds);

  sock.ev.on("connection.update", (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      session.qr = qr;
      session.status = "qr";
    }

    if (connection === "open") {
      session.status = "open";
      session.qr = null;
      console.log(`Teacher WhatsApp session ${teacherId} connected.`);
    }

    if (connection === "close") {
      const statusCode = (lastDisconnect?.error as Boom | undefined)?.output?.statusCode;
      if (statusCode === DisconnectReason.loggedOut) {
        session.status = "closed";
        session.qr = null;
        session.sock = null;
        console.log(`Teacher WhatsApp session ${teacherId} logged out.`);
      } else {
        session.status = "connecting";
        // Must clear this before retrying - startSession()'s "already in
        // progress" guard checks session.sock, and a stale dead socket
        // reference there would make it silently no-op the reconnect.
        session.sock = null;
        console.log(`Teacher WhatsApp session ${teacherId} closed, reconnecting...`, statusCode);
        startSession(teacherId);
      }
    }
  });
}

export async function logoutSession(rawTeacherId: string): Promise<void> {
  const teacherId = sanitizeId(rawTeacherId);
  const session = sessions.get(teacherId);
  if (session?.sock) {
    try {
      await session.sock.logout();
    } catch {
      // Already logged out / unreachable - fine, we're tearing it down anyway.
    }
  }
  sessions.delete(teacherId);
  // Without this, a later startSession() would try to reuse now-invalid
  // creds and just spin in the "connecting" -> "closed" loop forever.
  await rm(`${AUTH_ROOT}/${teacherId}`, { recursive: true, force: true });
}

interface GroupSummary {
  id: string;
  name: string;
  participantCount: number;
}

export async function listGroups(rawTeacherId: string): Promise<GroupSummary[]> {
  const teacherId = sanitizeId(rawTeacherId);
  const session = sessions.get(teacherId);
  if (!session?.sock || session.status !== "open") {
    throw new Error("WhatsApp session is not connected.");
  }

  const groups = await session.sock.groupFetchAllParticipating();
  return Object.values(groups).map((meta) => ({
    id: meta.id,
    name: meta.subject,
    participantCount: meta.participants.length,
  }));
}

const PHONE_JID_PATTERN = /^(\d+)@s\.whatsapp\.net$/;

export async function listGroupParticipants(rawTeacherId: string, groupId: string): Promise<string[]> {
  const teacherId = sanitizeId(rawTeacherId);
  const session = sessions.get(teacherId);
  if (!session?.sock || session.status !== "open") {
    throw new Error("WhatsApp session is not connected.");
  }

  const meta = await session.sock.groupMetadata(groupId);
  const numbers: string[] = [];
  for (const participant of meta.participants) {
    // participant.id can be a @lid (anonymous) JID in newer "LID" privacy
    // mode groups - participant.jid is what Baileys normalizes to the real
    // phone-number JID regardless of addressing mode, so prefer that.
    const match = PHONE_JID_PATTERN.exec(participant.jid ?? participant.id);
    if (match) numbers.push(match[1]);
  }
  return numbers;
}

