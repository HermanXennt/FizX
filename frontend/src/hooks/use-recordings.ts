"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { recordingService } from "@/services/recording-service";

export function useMyRecordings() {
  return useQuery({ queryKey: ["recordings", "mine"], queryFn: recordingService.mine });
}

export function useMeetingRecordings(meetingId: string | undefined) {
  return useQuery({
    queryKey: ["recordings", "meeting", meetingId],
    queryFn: () => recordingService.forMeeting(meetingId as string),
    enabled: Boolean(meetingId),
  });
}

export function useStartRecording(meetingId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => recordingService.start(meetingId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["recordings", "meeting", meetingId] }),
  });
}

export function useStopRecording(meetingId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (recordingId: string) => recordingService.stop(recordingId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["recordings", "meeting", meetingId] }),
  });
}
