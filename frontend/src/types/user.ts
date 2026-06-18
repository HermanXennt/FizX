export type PresenceStatus = "online" | "away" | "do_not_disturb" | "in_call" | "offline";

export interface NotificationPreferences {
  email_on_invite: boolean;
  email_on_meeting_reminder: boolean;
  email_on_recording_ready: boolean;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  initials: string;
  avatar_url: string | null;
  is_verified: boolean;
  presence_status: PresenceStatus;
  timezone: string;
  notification_preferences: NotificationPreferences;
  created_at: string;
}

export interface PublicUser {
  id: string;
  full_name: string;
  initials: string;
  avatar_url: string | null;
  presence_status: PresenceStatus;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface AuthResponse extends AuthTokens {
  user: User;
}
