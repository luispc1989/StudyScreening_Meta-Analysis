import { createFileRoute } from "@tanstack/react-router";
import { getStoredUser } from "@/lib/auth";
import { ThemeSwitcher } from "@/components/ThemeSwitcher";
import {
  User, Mail, Database as DbIcon, Palette, Clock, Link as LinkIcon,
  Monitor, Shield, Globe, ChevronRight
} from "lucide-react";

export const Route = createFileRoute("/app/settings")({
  head: () => ({
    meta: [
      { title: "Settings — PrismaLab" },
    ],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  const user = getStoredUser();

  return (
    <div className="p-6 xl:p-8 max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-xl font-medium text-foreground">Settings</h1>
        <p className="text-sm text-muted-foreground mt-1">Manage your account, preferences, and integrations</p>
      </div>

      {/* Account */}
      <SettingsSection title="Account Information" icon={<User className="h-4 w-4" />}>
        <SettingsRow label="Full name" value={user?.fullName || "—"} />
        <SettingsRow label="Username" value={user?.username || "—"} />
        <SettingsRow label="Email" value={user?.email || "—"} />
        <SettingsRow label="Password" value="••••••••" action="Change" />
      </SettingsSection>

      {/* Email Integration */}
      <SettingsSection title="Email Integration" icon={<Mail className="h-4 w-4" />}>
        <div className="px-5 py-4 text-sm text-muted-foreground">
          <p>Email integration will allow PrismaLab to send messages directly from your workspace — for example, contacting authors during screening workflows.</p>
          <div className="mt-4 space-y-2">
            <ProviderRow name="Google" status="Not connected" />
            <ProviderRow name="Outlook" status="Not connected" />
            <ProviderRow name="SMTP" status="Not configured" />
          </div>
        </div>
      </SettingsSection>

      {/* Local Database */}
      <SettingsSection title="Local Database & Projects" icon={<DbIcon className="h-4 w-4" />}>
        <SettingsRow label="Storage location" value="Default (local)" />
        <SettingsRow label="Database size" value="—" />
        <SettingsRow label="Active projects" value="0" />
        <SettingsRow label="Auto-backup" value="Enabled" action="Configure" />
      </SettingsSection>

      {/* Theme */}
      <SettingsSection title="Appearance" icon={<Palette className="h-4 w-4" />}>
        <div className="px-5 py-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Theme</p>
              <p className="text-xs text-muted-foreground mt-0.5">Choose between light, dark, or system preference</p>
            </div>
            <ThemeSwitcher />
          </div>
        </div>
      </SettingsSection>

      {/* Session */}
      <SettingsSection title="Session Behaviour" icon={<Clock className="h-4 w-4" />}>
        <SettingsRow label="Remember me" value="Active" action="Manage" />
        <SettingsRow label="Session timeout" value="Never (local app)" />
        <SettingsRow label="Auto-save interval" value="30 seconds" action="Change" />
      </SettingsSection>

      {/* App Preferences */}
      <SettingsSection title="App Preferences" icon={<Monitor className="h-4 w-4" />}>
        <SettingsRow label="Language" value="English" />
        <SettingsRow label="Date format" value="DD/MM/YYYY" action="Change" />
        <SettingsRow label="Default export format" value="Excel (.xlsx)" action="Change" />
        <SettingsRow label="Ray Research Assistant" value="Enabled" action="Configure" />
      </SettingsSection>
    </div>
  );
}

function SettingsSection({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      <div className="flex items-center gap-2 px-5 py-3 border-b border-border bg-secondary/50">
        <span className="text-muted-foreground">{icon}</span>
        <h2 className="text-xs font-medium tracking-[0.15em] uppercase text-muted-foreground">{title}</h2>
      </div>
      {children}
    </div>
  );
}

function SettingsRow({ label, value, action }: { label: string; value: string; action?: string }) {
  return (
    <div className="flex items-center justify-between px-5 py-3 border-b border-border last:border-b-0">
      <div>
        <p className="text-sm text-foreground">{label}</p>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-sm text-muted-foreground">{value}</span>
        {action && (
          <button className="text-xs text-brand-deep hover:text-brand font-medium transition-colors">
            {action}
          </button>
        )}
      </div>
    </div>
  );
}

function ProviderRow({ name, status }: { name: string; status: string }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border px-4 py-3">
      <div className="flex items-center gap-2">
        <Globe className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm">{name}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground">{status}</span>
        <button className="text-xs text-brand-deep hover:text-brand font-medium">Connect</button>
      </div>
    </div>
  );
}
