"use client";

import { useState } from "react";
import { Sparkle, GraduationCap, Presentation } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useRequestOtp, useVerifyOtp } from "@/hooks/use-auth";
import { extractErrorMessage } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import type { AccountType } from "@/types/user";

export default function LoginPage() {
  const [step, setStep] = useState<"phone" | "code">("phone");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [firstName, setFirstName] = useState("");
  const [accountType, setAccountType] = useState<AccountType | "">("");
  const [code, setCode] = useState("");

  const requestOtp = useRequestOtp();
  const verifyOtp = useVerifyOtp();

  function handleSendCode(e: React.FormEvent) {
    e.preventDefault();
    requestOtp.mutate(phoneNumber, { onSuccess: () => setStep("code") });
  }

  function handleVerify(e: React.FormEvent) {
    e.preventDefault();
    verifyOtp.mutate({
      phone_number: phoneNumber,
      code,
      first_name: firstName,
      account_type: accountType || undefined,
    });
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-soft">
            <Sparkle className="h-5 w-5" strokeWidth={2.25} fill="currentColor" />
          </div>
          <h1 className="text-[22px] font-semibold tracking-tight text-foreground">
            {step === "phone" ? "Welcome to FizX" : "Enter your code"}
          </h1>
          <p className="text-center text-[14px] text-muted-foreground">
            {step === "phone"
              ? "Sign in or create an account with WhatsApp"
              : `We sent a code over WhatsApp to ${phoneNumber}`}
          </p>
        </div>

        {step === "phone" ? (
          <form
            onSubmit={handleSendCode}
            className="flex flex-col gap-4 rounded-[28px] border border-black/5 bg-white p-5 sm:p-7 shadow-soft"
          >
            <div className="flex flex-col gap-1.5">
              <label className="text-[13px] font-medium text-foreground/80">Phone number</label>
              <Input
                type="tel"
                required
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder="15551234567"
                className="h-11 rounded-2xl border-black/10"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-[13px] font-medium text-foreground/80">
                Name <span className="text-muted-foreground">(only needed if you&apos;re new)</span>
              </label>
              <Input
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                placeholder="Jane"
                className="h-11 rounded-2xl border-black/10"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-[13px] font-medium text-foreground/80">
                I am a… <span className="text-muted-foreground">(only needed if you&apos;re new)</span>
              </label>
              <div className="grid grid-cols-2 gap-2.5">
                <button
                  type="button"
                  onClick={() => setAccountType("teacher")}
                  className={cn(
                    "flex flex-col items-center gap-1.5 rounded-2xl border px-3 py-3 transition-colors",
                    accountType === "teacher"
                      ? "border-primary bg-primary/5 text-foreground"
                      : "border-black/10 text-muted-foreground hover:bg-accent"
                  )}
                >
                  <Presentation className="h-4.5 w-4.5" strokeWidth={2} />
                  <span className="text-[13px] font-medium">Teacher</span>
                </button>
                <button
                  type="button"
                  onClick={() => setAccountType("student")}
                  className={cn(
                    "flex flex-col items-center gap-1.5 rounded-2xl border px-3 py-3 transition-colors",
                    accountType === "student"
                      ? "border-primary bg-primary/5 text-foreground"
                      : "border-black/10 text-muted-foreground hover:bg-accent"
                  )}
                >
                  <GraduationCap className="h-4.5 w-4.5" strokeWidth={2} />
                  <span className="text-[13px] font-medium">Student</span>
                </button>
              </div>
            </div>

            {requestOtp.isError && (
              <p className="rounded-xl bg-red-50 px-3 py-2 text-[12.5px] text-red-600">
                {extractErrorMessage(requestOtp.error)}
              </p>
            )}

            <Button
              type="submit"
              disabled={requestOtp.isPending}
              className="mt-1 h-11 rounded-full bg-primary text-primary-foreground shadow-soft hover:bg-primary/90"
            >
              {requestOtp.isPending ? "Sending…" : "Send code"}
            </Button>
          </form>
        ) : (
          <form
            onSubmit={handleVerify}
            className="flex flex-col gap-4 rounded-[28px] border border-black/5 bg-white p-5 sm:p-7 shadow-soft"
          >
            <div className="flex flex-col gap-1.5">
              <label className="text-[13px] font-medium text-foreground/80">Verification code</label>
              <Input
                required
                maxLength={6}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="123456"
                className="h-11 rounded-2xl border-black/10 text-center text-[18px] tracking-[0.3em]"
              />
            </div>

            {verifyOtp.isError && (
              <p className="rounded-xl bg-red-50 px-3 py-2 text-[12.5px] text-red-600">
                {extractErrorMessage(verifyOtp.error)}
              </p>
            )}

            <Button
              type="submit"
              disabled={verifyOtp.isPending}
              className="mt-1 h-11 rounded-full bg-primary text-primary-foreground shadow-soft hover:bg-primary/90"
            >
              {verifyOtp.isPending ? "Verifying…" : "Verify & continue"}
            </Button>

            <button
              type="button"
              onClick={() => setStep("phone")}
              className="text-[13px] text-muted-foreground hover:text-foreground"
            >
              Use a different number
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
