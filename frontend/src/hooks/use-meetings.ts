"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { meetingService } from "@/services/meeting-service";
import type { CreateInstantMeetingPayload, ScheduleMeetingPayload } from "@/types/meeting";

export function useIceServers() {
  return useQuery({
    queryKey: ["meetings", "ice-servers"],
    queryFn: meetingService.iceServers,
    staleTime: 12 * 60 * 60 * 1000, // credentials are valid for 24h server-side
  });
}

export function useMeetings(params?: { status?: string; workspace?: string }) {
  return useQuery({
    queryKey: ["meetings", params],
    queryFn: () => meetingService.list(params),
  });
}

export function useMeeting(id: string | undefined) {
  return useQuery({
    queryKey: ["meetings", id],
    queryFn: () => meetingService.retrieve(id as string),
    enabled: Boolean(id),
  });
}

export function useMeetingParticipants(id: string | undefined, options?: { pollMs?: number }) {
  return useQuery({
    queryKey: ["meetings", id, "participants"],
    queryFn: () => meetingService.participants(id as string),
    enabled: Boolean(id),
    refetchInterval: options?.pollMs,
  });
}

export function useCreateInstantMeeting() {
  const router = useRouter();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateInstantMeetingPayload = {}) => meetingService.createInstant(payload),
    onSuccess: (meeting) => {
      queryClient.invalidateQueries({ queryKey: ["meetings"] });
      router.push(`/call/${meeting.id}`);
    },
  });
}

export function useScheduleMeeting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ScheduleMeetingPayload) => meetingService.schedule(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["meetings"] }),
  });
}

export function useCancelMeeting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => meetingService.cancel(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["meetings"] }),
  });
}

export function useEndMeeting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => meetingService.end(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["meetings"] }),
  });
}

export function useJoinMeeting() {
  return useMutation({
    mutationFn: ({ id, password }: { id: string; password?: string }) => meetingService.join(id, password),
  });
}

export function useAdmitParticipant(meetingId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (participantId: string) => meetingService.admitParticipant(meetingId, participantId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["meetings", meetingId, "participants"] }),
  });
}

export function useDenyParticipant(meetingId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (participantId: string) => meetingService.denyParticipant(meetingId, participantId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["meetings", meetingId, "participants"] }),
  });
}

export function useRemoveParticipant(meetingId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (participantId: string) => meetingService.removeParticipant(meetingId, participantId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["meetings", meetingId, "participants"] }),
  });
}

export function useMuteAll(meetingId: string) {
  return useMutation({ mutationFn: () => meetingService.muteAll(meetingId) });
}

export function useSetParticipantMedia(meetingId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      participantId,
      ...payload
    }: { participantId: string; mic_enabled?: boolean; camera_enabled?: boolean }) =>
      meetingService.setParticipantMedia(meetingId, participantId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["meetings", meetingId, "participants"] }),
  });
}

export function useSyncPermissions(meetingId: string) {
  return useMutation({ mutationFn: () => meetingService.syncPermissions(meetingId) });
}

export function useRaiseHand(meetingId: string) {
  return useMutation({ mutationFn: (raised: boolean) => meetingService.raiseHand(meetingId, raised) });
}

export function useMarkSpoken(meetingId: string) {
  return useMutation({ mutationFn: () => meetingService.markSpoken(meetingId) });
}
