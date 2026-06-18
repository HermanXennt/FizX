import { AuthGuard } from "@/components/auth/auth-guard";
import { Sidebar } from "@/components/layout/sidebar";
import { MobileTabBar } from "@/components/layout/mobile-tab-bar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <div className="min-h-screen w-full bg-background">
        <Sidebar />
        {/* Bottom padding clears the fixed MobileTabBar below lg, where the
            sidebar (and its own padding allowance) isn't present. */}
        <main className="mx-auto max-w-[1400px] px-4 py-6 pb-24 sm:px-6 sm:py-8 sm:pb-8 lg:pl-[136px] lg:pr-10">
          {children}
        </main>
        <MobileTabBar />
      </div>
    </AuthGuard>
  );
}
