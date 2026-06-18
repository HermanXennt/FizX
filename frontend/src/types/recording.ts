import type { PublicUser } from "./user";

export type RecordingStatus = "processing" | "ready" | "failed";

export interface MeetingRecording {
  id: string;
  meeting: string;
  requested_by: PublicUser;
  status: RecordingStatus;
  file_url: string;
  duration_seconds: number | null;
  size_bytes: number | null;
  started_at: string | null;
  ended_at: string | null;
  error_message: string;
  created_at: string;
}
