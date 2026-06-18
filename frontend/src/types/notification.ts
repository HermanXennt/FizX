export type NotificationType =
  | "meeting_invite"
  | "meeting_reminder"
  | "meeting_starting"
  | "workspace_invite"
  | "recording_ready"
  | "mentioned_in_chat"
  | "role_changed"
  | "generic";

export interface AppNotification {
  id: string;
  type: NotificationType;
  title: string;
  body: string;
  data: Record<string, unknown>;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}
