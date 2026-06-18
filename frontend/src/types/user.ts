export type PresenceStatus = "online" | "away" | "do_not_disturb" | "in_call" | "offline";

export interface User {
  id: string;
  phone_number: string;
  first_name: string;
  last_name: string;
  full_name: string;
  initials: string;
  avatar_url: string | null;
  presence_status: PresenceStatus;
  timezone: string;
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
