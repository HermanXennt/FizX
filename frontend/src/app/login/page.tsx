"use client";

import Link from "next/link";
import { useState } from "react";
import { Sparkle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useLogin } from "@/hooks/use-auth";
import { extractErrorMessage } from "@/lib/api-client";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const login = useLogin();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    login.mutate({ email, password });
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-soft">
            <Sparkle className="h-5 w-5" strokeWidth={2.25} fill="currentColor" />
          </div>
          <h1 className="text-[22px] font-semibold tracking-tight text-foreground">Welcome back</h1>
          <p className="text-[14px] text-muted-foreground">Sign in to your FizX workspace</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="flex flex-col gap-4 rounded-[28px] border border-black/5 bg-white p-7 shadow-soft"
        >
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
            <div className="flex items-center justify-between">
              <label className="text-[13px] font-medium text-foreground/80">Password</label>
              <Link href="/forgot-password" className="text-[12px] text-muted-foreground hover:text-foreground">
                Forgot password?
              </Link>
            </div>
            <Input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="h-11 rounded-2xl border-black/10"
            />
          </div>

          {login.isError && (
            <p className="rounded-xl bg-red-50 px-3 py-2 text-[12.5px] text-red-600">
              {extractErrorMessage(login.error)}
            </p>
          )}

          <Button
            type="submit"
            disabled={login.isPending}
            className="mt-1 h-11 rounded-full bg-primary text-primary-foreground shadow-soft hover:bg-primary/90"
          >
            {login.isPending ? "Signing in…" : "Sign in"}
          </Button>
        </form>

        <p className="mt-6 text-center text-[13.5px] text-muted-foreground">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="font-medium text-foreground hover:underline">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
