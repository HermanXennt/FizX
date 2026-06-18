import type { PublicUser } from "./user";

export type WorkspaceRole = "owner" | "admin" | "member";
export type WorkspacePlan = "free" | "pro" | "enterprise";
export type InvitationStatus = "pending" | "accepted" | "declined" | "revoked" | "expired";

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  description: string;
  avatar_url: string | null;
  plan: WorkspacePlan;
  config: Record<string, boolean>;
  member_count: number;
  my_role: WorkspaceRole | null;
  created_at: string;
}

export interface WorkspaceMember {
  id: string;
  user: PublicUser;
  role: WorkspaceRole;
  created_at: string;
}

export interface Invitation {
  id: string;
  email: string;
  role: WorkspaceRole;
  status: InvitationStatus;
  invited_by: PublicUser;
  expires_at: string;
  created_at: string;
}
