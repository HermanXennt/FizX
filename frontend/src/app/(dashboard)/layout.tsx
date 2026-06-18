import { AuthGuard } from "@/components/auth/auth-guard";
import { Sidebar } from "@/components/layout/sidebar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <div className="min-h-screen w-full bg-background">
        <Sidebar />
        <main className="mx-auto max-w-[1400px] px-6 py-8 lg:pl-[136px] lg:pr-10">
          {children}
        </main>
      </div>
    </AuthGuard>
  );
}
