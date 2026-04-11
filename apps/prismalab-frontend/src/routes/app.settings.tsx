import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { getStoredUser } from "@/lib/auth";
import { getDefaultRaySettings, loadRaySettings, saveRaySettings, type RaySettings } from "@/lib/ray-settings";
import { ThemeSwitcher } from "@/components/ThemeSwitcher";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  User, Mail, Database as DbIcon, Palette, Clock, Monitor, Bot,
} from "lucide-react";

export const Route = createFileRoute("/app/settings")({
  head: () => ({
    meta: [{ title: "Settings - PrismaLab" }],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  const user = getStoredUser();
  const [raySettings, setRaySettings] = useState<RaySettings>(getDefaultRaySettings());
  const [savedMessage, setSavedMessage] = useState("");

  useEffect(() => {
    setRaySettings(loadRaySettings(user?.username));
  }, [user?.username]);

  const updateRaySettings = <K extends keyof RaySettings>(key: K, value: RaySettings[K]) => {
    setSavedMessage("");
    setRaySettings((current) => ({ ...current, [key]: value }));
  };

  const handleSaveRaySettings = () => {
    if (!user?.username) return;
    saveRaySettings(user.username, raySettings);
    setSavedMessage("Ray integration settings saved locally for this account.");
  };

  return (
    <div className="mx-auto max-w-4xl space-y-8 p-6 xl:p-8">
      <div>
        <h1 className="text-xl font-medium text-foreground">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">Manage your profile, preferences, and integrations</p>
      </div>

      <SettingsSection title="Profile Information" icon={<User className="h-4 w-4" />}>
        <SettingsRow label="Full name" value={user?.fullName || "-"} />
        <SettingsRow label="Username" value={user?.username || "-"} />
        <SettingsRow label="Email" value={user?.email || "-"} />
        <SettingsRow label="Password" value="••••••••" action="Managed from access flow" />
      </SettingsSection>

      <SettingsSection title="Ray Integration" icon={<Bot className="h-4 w-4" />}>
        <div className="space-y-6 px-5 py-4">
          <div className="space-y-1">
            <p className="text-sm font-medium text-foreground">Provider mode</p>
            <p className="text-xs leading-relaxed text-muted-foreground">
              Choose whether Ray runs against a local Ollama instance or an Ollama API endpoint for this account.
            </p>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <button
              type="button"
              onClick={() => updateRaySettings("mode", "ollama-local")}
              className={`rounded-xl border px-4 py-4 text-left transition-colors ${
                raySettings.mode === "ollama-local"
                  ? "border-brand bg-brand/10"
                  : "border-border bg-card hover:bg-accent"
              }`}
            >
              <p className="text-sm font-medium text-foreground">Ollama local</p>
              <p className="mt-1 text-xs text-muted-foreground">Use a local Ollama runtime on this machine.</p>
            </button>
            <button
              type="button"
              onClick={() => updateRaySettings("mode", "ollama-api")}
              className={`rounded-xl border px-4 py-4 text-left transition-colors ${
                raySettings.mode === "ollama-api"
                  ? "border-brand bg-brand/10"
                  : "border-border bg-card hover:bg-accent"
              }`}
            >
              <p className="text-sm font-medium text-foreground">Ollama via API</p>
              <p className="mt-1 text-xs text-muted-foreground">Use an API-backed Ollama account for machines that cannot run models locally.</p>
            </button>
          </div>

          {raySettings.mode === "ollama-local" ? (
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="ray-local-endpoint" className="text-xs font-medium uppercase tracking-[0.22em] text-muted-foreground">
                  Local endpoint
                </Label>
                <Input
                  id="ray-local-endpoint"
                  value={raySettings.localEndpoint}
                  onChange={(event) => updateRaySettings("localEndpoint", event.target.value)}
                  className="h-12 rounded-xl"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="ray-local-model" className="text-xs font-medium uppercase tracking-[0.22em] text-muted-foreground">
                  Local model
                </Label>
                <Input
                  id="ray-local-model"
                  value={raySettings.localModel}
                  onChange={(event) => updateRaySettings("localModel", event.target.value)}
                  className="h-12 rounded-xl"
                />
              </div>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="ray-api-endpoint" className="text-xs font-medium uppercase tracking-[0.22em] text-muted-foreground">
                  API endpoint
                </Label>
                <Input
                  id="ray-api-endpoint"
                  value={raySettings.apiEndpoint}
                  onChange={(event) => updateRaySettings("apiEndpoint", event.target.value)}
                  className="h-12 rounded-xl"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="ray-api-key" className="text-xs font-medium uppercase tracking-[0.22em] text-muted-foreground">
                  API key
                </Label>
                <Input
                  id="ray-api-key"
                  type="password"
                  value={raySettings.apiKey}
                  onChange={(event) => updateRaySettings("apiKey", event.target.value)}
                  placeholder="Paste your Ollama API key"
                  className="h-12 rounded-xl"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="ray-api-model" className="text-xs font-medium uppercase tracking-[0.22em] text-muted-foreground">
                  API model
                </Label>
                <Input
                  id="ray-api-model"
                  value={raySettings.apiModel}
                  onChange={(event) => updateRaySettings("apiModel", event.target.value)}
                  className="h-12 rounded-xl"
                />
              </div>
            </div>
          )}

          <div className="flex items-center justify-between gap-4 rounded-xl border border-border bg-secondary/40 px-4 py-3">
            <p className="text-xs leading-relaxed text-muted-foreground">
              These settings stay local to the current PrismaLab account and will later drive how Ray connects to the chosen Ollama provider.
            </p>
            <Button type="button" onClick={handleSaveRaySettings} className="rounded-xl">
              Save Ray settings
            </Button>
          </div>

          {savedMessage ? (
            <div className="rounded-xl border border-brand/20 bg-brand/10 px-4 py-3 text-sm text-brand-deep dark:text-brand">
              {savedMessage}
            </div>
          ) : null}
        </div>
      </SettingsSection>

      <SettingsSection title="Email Integration" icon={<Mail className="h-4 w-4" />}>
        <div className="px-5 py-4 text-sm text-muted-foreground">
          Email integration will allow PrismaLab to contact authors and support workflow communications from inside the workspace.
        </div>
      </SettingsSection>

      <SettingsSection title="Local Database & Projects" icon={<DbIcon className="h-4 w-4" />}>
        <SettingsRow label="Storage location" value="Default (local)" />
        <SettingsRow label="Database size" value="-" />
        <SettingsRow label="Active projects" value="0" />
        <SettingsRow label="Auto-backup" value="Enabled" action="Configure" />
      </SettingsSection>

      <SettingsSection title="Appearance" icon={<Palette className="h-4 w-4" />}>
        <div className="px-5 py-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Theme</p>
              <p className="mt-0.5 text-xs text-muted-foreground">Choose between light, dark, or system preference</p>
            </div>
            <ThemeSwitcher />
          </div>
        </div>
      </SettingsSection>

      <SettingsSection title="Session Behaviour" icon={<Clock className="h-4 w-4" />}>
        <SettingsRow label="Remember me" value="Active" action="Manage" />
        <SettingsRow label="Session timeout" value="Never (local app)" />
        <SettingsRow label="Auto-save interval" value="30 seconds" action="Change" />
      </SettingsSection>

      <SettingsSection title="App Preferences" icon={<Monitor className="h-4 w-4" />}>
        <SettingsRow label="Language" value="English" />
        <SettingsRow label="Date format" value="DD/MM/YYYY" action="Change" />
        <SettingsRow label="Default export format" value="Excel (.xlsx)" action="Change" />
        <SettingsRow label="Ray Research Assistant" value="Enabled" action="Configured below" />
      </SettingsSection>
    </div>
  );
}

function SettingsSection({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="overflow-hidden rounded-xl border border-border bg-card">
      <div className="flex items-center gap-2 border-b border-border bg-secondary/50 px-5 py-3">
        <span className="text-muted-foreground">{icon}</span>
        <h2 className="text-xs font-medium uppercase tracking-[0.15em] text-muted-foreground">{title}</h2>
      </div>
      {children}
    </div>
  );
}

function SettingsRow({ label, value, action }: { label: string; value: string; action?: string }) {
  return (
    <div className="flex items-center justify-between border-b border-border px-5 py-3 last:border-b-0">
      <p className="text-sm text-foreground">{label}</p>
      <div className="flex items-center gap-3">
        <span className="text-sm text-muted-foreground">{value}</span>
        {action ? <button className="text-xs font-medium text-brand-deep transition-colors hover:text-brand">{action}</button> : null}
      </div>
    </div>
  );
}
