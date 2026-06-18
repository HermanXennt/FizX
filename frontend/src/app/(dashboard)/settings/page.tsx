"use client";

import { useRef, useState } from "react";
import { Topbar } from "@/components/layout/topbar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { authService } from "@/services/auth-service";
import { useAuthStore } from "@/store/auth-store";
import { extractErrorMessage } from "@/lib/api-client";

export default function SettingsPage() {
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [firstName, setFirstName] = useState(user?.first_name ?? "");
  const [lastName, setLastName] = useState(user?.last_name ?? "");
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMessage, setProfileMessage] = useState<string | null>(null);

  async function handleSaveProfile(e: React.FormEvent) {
    e.preventDefault();
    setProfileSaving(true);
    setProfileMessage(null);
    try {
      const updated = await authService.updateProfile({ first_name: firstName, last_name: lastName });
      setUser(updated);
      setProfileMessage("Profile updated.");
    } catch (error) {
      setProfileMessage(extractErrorMessage(error));
    } finally {
      setProfileSaving(false);
    }
  }

  async function handleAvatarChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const updated = await authService.uploadAvatar(file);
    setUser(updated);
  }

  return (
    <>
      <Topbar title="Settings" subtitle="Manage your profile and account." />

      <div className="mx-auto max-w-xl">
        <div className="rounded-[28px] border border-black/5 bg-white p-5 sm:p-7 shadow-soft">
          <h3 className="mb-5 text-[16px] font-semibold tracking-tight text-foreground">Profile</h3>

          <div className="mb-5 flex items-center gap-4">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex h-16 w-16 items-center justify-center overflow-hidden rounded-full bg-[#1d1d1f] text-[18px] font-semibold text-white"
            >
              {user?.avatar_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={user.avatar_url} alt="" className="h-full w-full object-cover" />
              ) : (
                user?.initials
              )}
            </button>
            <div>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="rounded-full border border-black/10 px-3 py-1.5 text-[12.5px] font-medium hover:bg-accent"
              >
                Change avatar
              </button>
              <input ref={fileInputRef} type="file" accept="image/*" hidden onChange={handleAvatarChange} />
            </div>
          </div>

          <form onSubmit={handleSaveProfile} className="flex flex-col gap-3">
            <div className="grid grid-cols-2 gap-3">
              <Input
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                placeholder="First name"
                className="h-10 rounded-2xl border-black/10"
              />
              <Input
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                placeholder="Last name"
                className="h-10 rounded-2xl border-black/10"
              />
            </div>
            <Input value={user?.phone_number ?? ""} disabled className="h-10 rounded-2xl border-black/10" />
            {profileMessage && <p className="text-[12.5px] text-muted-foreground">{profileMessage}</p>}
            <Button
              type="submit"
              disabled={profileSaving}
              className="h-10 w-fit rounded-full bg-primary text-primary-foreground"
            >
              {profileSaving ? "Saving…" : "Save changes"}
            </Button>
          </form>
        </div>
      </div>
    </>
  );
}
