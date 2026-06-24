"use client";

import { Topbar } from "@/components/layout/topbar";
import { ChatLauncher } from "@/components/dashboard/chat-launcher";
import { StudentDashboard } from "@/components/dashboard/student-dashboard";
import { TeacherDashboard } from "@/components/dashboard/teacher-dashboard";
import { useAuthStore } from "@/store/auth-store";

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);

  return (
    <>
      <Topbar />

      {user?.account_type === "teacher" ? <TeacherDashboard /> : <StudentDashboard />}

      <ChatLauncher />
    </>
  );
}
