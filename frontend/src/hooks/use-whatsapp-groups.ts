"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { whatsappGroupsService } from "@/services/whatsapp-groups-service";

export function useWhatsAppStatus(options?: { pollMs?: number; enabled?: boolean }) {
  return useQuery({
    queryKey: ["whatsapp-groups", "status"],
    queryFn: whatsappGroupsService.status,
    enabled: options?.enabled ?? true,
    refetchInterval: options?.pollMs,
  });
}

export function useWhatsAppQr(enabled: boolean) {
  return useQuery({
    queryKey: ["whatsapp-groups", "qr"],
    queryFn: whatsappGroupsService.qr,
    enabled,
    refetchInterval: enabled ? 4000 : undefined,
  });
}

export function useWhatsAppGroups(enabled: boolean) {
  return useQuery({
    queryKey: ["whatsapp-groups", "groups"],
    queryFn: whatsappGroupsService.groups,
    enabled,
  });
}

export function useConnectWhatsApp() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: whatsappGroupsService.connect,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["whatsapp-groups", "status"] }),
  });
}

export function useDisconnectWhatsApp() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: whatsappGroupsService.disconnect,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["whatsapp-groups"] }),
  });
}

export function useImportWhatsAppGroup(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ groupId, groupName }: { groupId: string; groupName: string }) =>
      whatsappGroupsService.importGroup(workspaceId, groupId, groupName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspaces", workspaceId, "members"] });
      queryClient.invalidateQueries({ queryKey: ["workspaces", workspaceId, "invitations"] });
      queryClient.invalidateQueries({ queryKey: ["workspaces"] });
    },
  });
}

export function useUnlinkWhatsAppGroup(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => whatsappGroupsService.unlinkGroup(workspaceId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["workspaces"] }),
  });
}
