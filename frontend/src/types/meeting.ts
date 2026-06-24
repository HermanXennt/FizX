import type { PublicUser } from "./user";

export type MeetingStatus = "scheduled" | "live" | "ended" | "cancelled";
export type ParticipantRole = "host" | "co_host" | "participant";
export type ParticipantStatus = "invited" | "waiting" | "admitted" | "left" | "denied" | "removed";

export interface Meeting {
  id: string;
  workspace: string | null;
  host: PublicUser;
  title: string;
  description: string;
  room_name: string;
  status: MeetingStatus;
  requires_password: boolean;
  waiting_room_enabled: boolean;
  max_participants: number;
  scheduled_start: string | null;
  scheduled_end: string | null;
  actual_start: string | null;
  actual_end: string | null;
  recurrence_rule: string;
  is_recurring_template: boolean;
  parent_meeting: string | null;
  participant_count: number;
  created_at: string;
}

export interface MeetingParticipant {
  id: string;
  user: PublicUser;
  role: ParticipantRole;
  status: ParticipantStatus;
  joined_at: string | null;
  left_at: string | null;
  is_muted: boolean;
  camera_disabled: boolean;
  hand_raised: boolean;
  has_spoken: boolean;
}

export interface JoinMeetingResponse {
  status: ParticipantStatus;
  token: string | null;
  livekit_url: string;
  participant: MeetingParticipant;
  meeting: Meeting;
}

export interface CreateInstantMeetingPayload {
  title?: string;
  workspace?: string;
  participant_ids?: string[];
}

export interface ScheduleMeetingPayload {
  title: string;
  description?: string;
  workspace?: string;
  scheduled_start: string;
  scheduled_end: string;
  password?: string;
  waiting_room_enabled?: boolean;
  max_participants?: number;
  recurrence_rule?: string;
}
