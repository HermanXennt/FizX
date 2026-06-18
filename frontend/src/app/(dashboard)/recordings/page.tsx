"use client";

import { Topbar } from "@/components/layout/topbar";
import { RecordingsList } from "@/components/dashboard/recordings-list";

export default function RecordingsPage() {
  return (
    <>
      <Topbar title="Recordings" subtitle="Playback and download recordings from meetings you've hosted or joined." />
      <div className="mx-auto max-w-3xl">
        <RecordingsList />
      </div>
    </>
  );
}
