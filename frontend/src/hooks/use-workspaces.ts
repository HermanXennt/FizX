"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { workspaceService } from "@/services/workspace-service";
import type { WorkspaceRole } from "@/types/workspace";

export function useWorkspaces() {
  return useQuery({ queryKey: ["workspaces"], queryFn: workspaceService.list });
}

export function useWorkspace(id: string | undefined) {
  return useQuery({
    queryKey: ["workspaces", id],
    queryFn: () => workspaceService.retrieve(id as string),
    enabled: Boolean(id),
  });
}

export function useWorkspaceMembers(id: string | undefined, search?: string) {
  return useQuery({
    queryKey: ["workspaces", id, "members", search ?? ""],
    queryFn: () => workspaceService.members(id as string, search),
    enabled: Boolean(id),
  });
}

export function useWorkspaceInvitations(id: string | undefined) {
  return useQuery({
    queryKey: ["workspaces", id, "invitations"],
    queryFn: () => workspaceService.invitations(id as string),
    enabled: Boolean(id),
  });
}

export function useCreateWorkspace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: workspaceService.create,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["workspaces"] }),
  });
}

export function useInviteToWorkspace(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ phone_number, role }: { phone_number: string; role: "admin" | "member" }) =>
      workspaceService.invite(workspaceId, phone_number, role),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["workspaces", workspaceId, "invitations"] }),
  });
}

export function useChangeMemberRole(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: WorkspaceRole }) =>
      workspaceService.changeMemberRole(workspaceId, userId, role),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["workspaces", workspaceId, "members"] }),
  });
}

export function useRemoveMember(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) => workspaceService.removeMember(workspaceId, userId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["workspaces", workspaceId, "members"] }),
  });
}

export function useAcceptInvitation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (token: string) => workspaceService.acceptInvitation(token),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["workspaces"] }),
  });
}

export function useDeclineInvitation() {
  return useMutation({
    mutationFn: (token: string) => workspaceService.declineInvitation(token),
  });
}
