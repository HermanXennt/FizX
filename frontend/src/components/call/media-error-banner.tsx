"use client";

import { MediaDeviceFailure } from "livekit-client";
import { AlertTriangle, X } from "lucide-react";

const MESSAGES: Record<MediaDeviceFailure, string> = {
  [MediaDeviceFailure.PermissionDenied]:
    "Camera/microphone access is blocked. Open your browser's site settings for this page and allow camera and microphone, then rejoin.",
  [MediaDeviceFailure.NotFound]:
    "No camera or microphone was found on this device.",
  [MediaDeviceFailure.DeviceInUse]:
    "Your camera or microphone is already in use by another app or browser tab.",
  [MediaDeviceFailure.Other]:
    "Couldn't access your camera or microphone.",
};

export function MediaErrorBanner({
  failure,
  onDismiss,
}: {
  failure: MediaDeviceFailure;
  onDismiss: () => void;
}) {
  return (
    <div className="absolute inset-x-3 top-3 z-50 flex items-start gap-2.5 rounded-2xl border border-amber-400/20 bg-[#26211a] px-4 py-3 text-amber-100 shadow-float sm:inset-x-auto sm:left-1/2 sm:top-4 sm:w-[420px] sm:-translate-x-1/2">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" strokeWidth={2} />
      <p className="flex-1 text-[13px] leading-snug">{MESSAGES[failure]}</p>
      <button
        onClick={onDismiss}
        className="shrink-0 rounded-full p-0.5 text-amber-100/60 hover:text-amber-100"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}
