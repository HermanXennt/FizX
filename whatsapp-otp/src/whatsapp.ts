import { Boom } from "@hapi/boom";
import makeWASocket, {
  useMultiFileAuthState,
  fetchLatestBaileysVersion,
  DisconnectReason,
  type WASocket,
} from "@whiskeysockets/baileys";
import pino from "pino";

const AUTH_DIR = process.env.WA_AUTH_DIR ?? "./auth";

const logger = pino({ level: "warn" });

export type ConnectionStatus = "connecting" | "qr" | "open" | "closed";

let sock: WASocket | null = null;
let currentQr: string | null = null;
let status: ConnectionStatus = "connecting";

export function getStatus(): ConnectionStatus {
  return status;
}

export function getQr(): string | null {
  return currentQr;
}

export function getSocket(): WASocket | null {
  return sock;
}

export async function startWhatsApp(): Promise<void> {
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
  // The version bundled with the package goes stale between releases; an
  // outdated version is what WhatsApp's servers reject the connection over.
  const { version } = await fetchLatestBaileysVersion();

  sock = makeWASocket({ auth: state, logger, version });

  sock.ev.on("creds.update", saveCreds);

  sock.ev.on("connection.update", (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      currentQr = qr;
      status = "qr";
    }

    if (connection === "open") {
      status = "open";
      currentQr = null;
      console.log("WhatsApp connected.");
    }

    if (connection === "close") {
      const statusCode = (lastDisconnect?.error as Boom | undefined)?.output?.statusCode;
      if (statusCode === DisconnectReason.loggedOut) {
        status = "closed";
        currentQr = null;
        console.log("WhatsApp logged out. Delete the auth folder and restart to link a new number.");
      } else {
        status = "connecting";
        console.log("WhatsApp connection closed, reconnecting...", statusCode);
        startWhatsApp();
      }
    }
  });
}

export function toJid(phone: string): string {
  const digits = phone.replace(/[^\d]/g, "");
  return `${digits}@s.whatsapp.net`;
}

export async function hasWhatsApp(jid: string): Promise<boolean> {
  if (!sock) return false;
  const results = await sock.onWhatsApp(jid);
  return Boolean(results?.[0]?.exists);
}

export async function sendText(jid: string, text: string): Promise<void> {
  if (!sock) throw new Error("WhatsApp socket is not initialized.");
  await sock.sendMessage(jid, { text });
}
