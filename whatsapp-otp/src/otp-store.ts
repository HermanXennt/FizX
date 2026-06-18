import { randomInt } from "crypto";

const OTP_TTL_MS = 5 * 60 * 1000;

interface OtpEntry {
  code: string;
  expiresAt: number;
}

const store = new Map<string, OtpEntry>();

export function generateOtp(): string {
  return randomInt(100000, 1000000).toString();
}

export function storeOtp(phone: string, code: string): void {
  store.set(phone, { code, expiresAt: Date.now() + OTP_TTL_MS });
}

export type VerifyResult = "valid" | "invalid" | "expired" | "not_found";

export function verifyOtp(phone: string, code: string): VerifyResult {
  const entry = store.get(phone);
  if (!entry) return "not_found";
  if (Date.now() > entry.expiresAt) {
    store.delete(phone);
    return "expired";
  }
  if (entry.code !== code) return "invalid";
  store.delete(phone);
  return "valid";
}
