export interface DayCount {
  date: string;
  count: number;
}

export interface TopHost {
  user_id: string;
  name: string;
  meeting_count: number;
}

export interface WorkspaceOverview {
  total_meetings: number;
  total_meeting_minutes: number;
  avg_meeting_duration_minutes: number;
  total_recordings: number;
  meetings_by_day: DayCount[];
  top_hosts: TopHost[];
}

export interface UserStats {
  meetings_hosted: number;
  meetings_attended: number;
  total_minutes_in_meetings: number;
  activity_by_day: DayCount[];
}
