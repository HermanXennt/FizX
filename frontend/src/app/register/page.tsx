"use client";

import Link from "next/link";
import { useState } from "react";
import { Sparkle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useRegister } from "@/hooks/use-auth";
import { extractErrorMessage } from "@/lib/api-client";

export default function RegisterPage() {
  const [firstName, setFirstName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const register = useRegister();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    register.mutate({ email, password, first_name: firstName });
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-soft">
            <Sparkle className="h-5 w-5" strokeWidth={2.25} fill="currentColor" />
          </div>
          <h1 className="text-[22px] font-semibold tracking-tight text-foreground">Create your account</h1>
          <p className="text-[14px] text-muted-foreground">Start hosting meetings in minutes</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="flex flex-col gap-4 rounded-[28px] border border-black/5 bg-white p-7 shadow-soft"
        >
          <div className="flex flex-col gap-1.5">
            <label className="text-[13px] font-medium text-foreground/80">First name</label>
            <Input
              required
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              placeholder="Jane"
              className="h-11 rounded-2xl border-black/10"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-[13px] font-medium text-foreground/80">Email</label>
            <Input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              className="h-11 rounded-2xl border-black/10"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-[13px] font-medium text-foreground/80">Password</label>
            <Input
              type="password"
              required
              minLength={10}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 10 characters"
              className="h-11 rounded-2xl border-black/10"
            />
          </div>

          {register.isError && (
            <p className="rounded-xl bg-red-50 px-3 py-2 text-[12.5px] text-red-600">
              {extractErrorMessage(register.error)}
            </p>
          )}

          <Button
            type="submit"
            disabled={register.isPending}
            className="mt-1 h-11 rounded-full bg-primary text-primary-foreground shadow-soft hover:bg-primary/90"
          >
            {register.isPending ? "Creating account…" : "Create account"}
          </Button>
        </form>

        <p className="mt-6 text-center text-[13.5px] text-muted-foreground">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-foreground hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
