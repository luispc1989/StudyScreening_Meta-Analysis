import { createFileRoute, Outlet, Link, useLocation } from "@tanstack/react-router";
import { useState } from "react";
import { PrismaLabLogo, PrismaLabMark } from "@/components/PrismaLabLogo";
import { ThemeSwitcher } from "@/components/ThemeSwitcher";
import { RayAssistant } from "@/components/RayAssistant";
import { getStoredUser, logout } from "@/lib/auth";
import {
  FileQuestion, Search, FileCheck, ShieldCheck, Database,
  BarChart3, MessageSquareText, Settings, LogOut, PanelLeft,
  Sparkles, ChevronRight,
} from "lucide-react";

export const Route = createFileRoute("/app")({
  component: AppShell,
});

const phases = [
  { id: "question", label: "Question Definition", icon: FileQuestion, color: "bg-spectrum-1" },
  { id: "search", label: "Literature Search", icon: Search, color: "bg-spectrum-2" },
  { id: "screening", label: "Study Screening", icon: FileCheck, color: "bg-spectrum-3" },
  { id: "appraisal", label: "Critical Appraisal", icon: ShieldCheck, color: "bg-spectrum-4" },
  { id: "extraction", label: "Data Extraction", icon: Database, color: "bg-spectrum-5" },
  { id: "synthesis", label: "Statistical Synthesis", icon: BarChart3, color: "bg-phase-synthesis" },
  { id: "discussion", label: "Discussion & Conclusion", icon: MessageSquareText, color: "bg-phase-discussion" },
];

function AppShell() {
  const [collapsed, setCollapsed] = useState(false);
  const [rayOpen, setRayOpen] = useState(false);
  const location = useLocation();
  const user = getStoredUser();

  const isActive = (path: string) => location.pathname.includes(path);

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside
        className={`flex flex-col border-r border-border bg-card transition-all duration-200 ease-out ${
          collapsed ? "w-16" : "w-64"
        }`}
      >
        {/* Logo */}
        <div className={`flex items-center border-b border-border ${collapsed ? "h-16 px-2" : "h-18 px-4"}`}>
          {collapsed ? (
            <PrismaLabMark size={44} className="mx-auto" />
          ) : (
            <PrismaLabLogo size="sm" className="w-full max-w-[14rem]" />
          )}
        </div>

        {/* Phase navigation */}
        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
          {!collapsed && (
            <span className="text-[10px] font-medium tracking-[0.2em] uppercase text-muted-foreground px-2 mb-2 block">
              Workflow Phases
            </span>
          )}
          {phases.map((phase) => {
            const Icon = phase.icon;
            const active = isActive(`/app/${phase.id}`);
            return (
              <Link
                key={phase.id}
                to="/app/$phaseId"
                params={{ phaseId: phase.id }}
                className={`flex items-center gap-3 rounded-lg px-2.5 py-2 text-sm transition-colors duration-120 ${
                  active
                    ? "bg-accent text-foreground font-medium"
                    : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                }`}
                title={collapsed ? phase.label : undefined}
              >
                <div className="relative flex-shrink-0">
                  <Icon className="h-4 w-4" />
                  <div className={`absolute -left-1 -top-1 h-1.5 w-1.5 rounded-full ${phase.color} ${active ? "opacity-100" : "opacity-40"}`} />
                </div>
                {!collapsed && <span className="truncate">{phase.label}</span>}
                {!collapsed && active && <ChevronRight className="h-3 w-3 ml-auto opacity-40" />}
              </Link>
            );
          })}
        </nav>

        {/* Bottom actions */}
        <div className="border-t border-border p-2 space-y-0.5">
          <Link
            to="/app/settings"
            className={`flex items-center gap-3 rounded-lg px-2.5 py-2 text-sm transition-colors ${
              isActive("/app/settings") ? "bg-accent text-foreground" : "text-muted-foreground hover:bg-secondary hover:text-foreground"
            }`}
          >
            <Settings className="h-4 w-4 flex-shrink-0" />
            {!collapsed && <span>Settings</span>}
          </Link>

          {!collapsed && user && (
            <div className="flex items-center gap-2 px-2.5 py-2 mt-2">
              <div className="h-7 w-7 rounded-full bg-brand/20 flex items-center justify-center text-xs font-medium text-brand-deep">
                {user.fullName.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium truncate">{user.fullName}</p>
                <p className="text-[10px] text-muted-foreground truncate">{user.username}</p>
              </div>
              <button
                onClick={() => { logout(); window.location.href = "/login"; }}
                className="text-muted-foreground hover:text-foreground"
                title="Sign out"
              >
                <LogOut className="h-3.5 w-3.5" />
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* Main content area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="flex items-center justify-between h-14 px-4 border-b border-border bg-background">
          <button onClick={() => setCollapsed(!collapsed)} className="text-muted-foreground hover:text-foreground">
            <PanelLeft className="h-4.5 w-4.5" />
          </button>
          <div className="flex items-center gap-3">
            <ThemeSwitcher compact />
          </div>
        </header>

        {/* Content + Ray panel */}
        <div className="flex-1 flex overflow-hidden">
          <main className="flex-1 overflow-y-auto">
            <Outlet />
          </main>

          {/* Ray Assistant Panel */}
          {rayOpen && <RayAssistant onClose={() => setRayOpen(false)} />}
        </div>

        <button
          type="button"
          onClick={() => setRayOpen(true)}
          className="absolute bottom-6 right-6 z-30 flex h-15 w-15 items-center justify-center rounded-full border border-border/80 bg-card/94 text-foreground shadow-[0_12px_32px_rgba(0,0,0,0.18)] backdrop-blur-md transition-all hover:scale-[1.02] hover:border-brand/30 hover:shadow-[0_16px_36px_rgba(0,0,0,0.22)]"
          aria-label="Open Ray Research Assistant"
          title="Open Ray Research Assistant"
        >
          <span className="absolute h-15 w-15 rounded-full border border-brand/10" />
          <span className="absolute h-10 w-10 rounded-full bg-brand/10" />
          <Sparkles className="relative h-6 w-6 text-brand-deep" />
        </button>
      </div>
    </div>
  );
}
