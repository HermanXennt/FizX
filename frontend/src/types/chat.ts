import type { PublicUser } from "./user";

export interface MessageReactionSummary {
  emoji: string;
  count: number;
  user_ids: string[];
}

export interface ChatMessage {
  id: string;
  channel: string;
  sender: PublicUser;
  content: string;
  attachment_url: string | null;
  reply_to_id: string | null;
  reactions: MessageReactionSummary[];
  is_deleted: boolean;
  edited_at: string | null;
  created_at: string;
}
