import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { PrismaLabLogo } from "@/components/PrismaLabLogo";
import { ThemeSwitcher } from "@/components/ThemeSwitcher";
import { PasswordField } from "@/components/PasswordField";
import { RecoveryKeyPanel } from "@/components/RecoveryKeyPanel";
import { listLocalProfiles, recoverAccess } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export const Route = createFileRoute("/recover")({
  head: () => ({
    meta: [
      { title: "Recover Access - PrismaLab" },
      { name: "description", content: "Recover access to your local PrismaLab account using a recovery key" },
    ],
  }),
  component: RecoverPage,
});

function RecoverPage() {
  const navigate = useNavigate();
  const profiles = useMemo(() => listLocalProfiles(), []);
  const [username, setUsername] = useState(profiles[0]?.username || "");
  const [recoveryKey, setRecoveryKey] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [recoveryState, setRecoveryState] = useState<{
    username: string;
    recoveryKey: string;
  } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;

    setError("");
    if (!username.trim() || !recoveryKey.trim() || !newPassword.trim() || !confirmPassword.trim()) {
      setError("Complete all recovery fields before continuing");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await recoverAccess({
        username,
        recoveryKey,
        newPassword,
      });
      if (!result) {
        setError("Recovery key or account details are invalid");
        return;
      }
      setRecoveryState({ username: result.user.username, recoveryKey: result.recoveryKey });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reset the password");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-background text-foreground">
      <div className="absolute inset-0 bg-white dark:bg-[#111111]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(93,202,165,0.05),transparent_30%),radial-gradient(circle_at_bottom,rgba(127,119,221,0.04),transparent_24%)] dark:bg-[radial-gradient(circle_at_top,rgba(93,202,165,0.07),transparent_30%),radial-gradient(circle_at_bottom,rgba(127,119,221,0.06),transparent_24%)]" />
      <div className="absolute inset-3 rounded-[2rem] border border-[#e7e2d8] bg-white/98 shadow-[0_18px_50px_rgba(40,34,24,0.05)] dark:border-[#1c1c1a] dark:bg-[#111111]/98 dark:shadow-[0_24px_80px_rgba(0,0,0,0.28)]" />
      <div className="pointer-events-none absolute left-1/2 top-[54%] h-[34rem] w-[46rem] -translate-x-1/2 -translate-y-1/2 rounded-[3rem] bg-[radial-gradient(circle,rgba(255,255,255,0.72)_0%,rgba(255,255,255,0.36)_48%,transparent_80%)] blur-3xl dark:bg-[radial-gradient(circle,rgba(26,26,26,0.42)_0%,rgba(17,17,17,0.12)_52%,transparent_82%)]" />

      <div className="relative flex min-h-screen flex-col">
        <div className="flex items-center justify-end p-6">
          <ThemeSwitcher compact />
        </div>

        <div className="flex flex-1 items-center justify-center px-6 pb-16">
          <div className="grid w-full max-w-[74rem] justify-items-center">
            <div className="mx-auto flex w-full max-w-7xl justify-center text-center">
              <PrismaLabLogo showTagline size="lg" tone="auto" className="w-full max-w-[64rem]" />
            </div>

            <div className="relative mx-auto mt-7 w-full max-w-[36rem] rounded-[1.75rem] border border-[#ece6da] bg-white/80 px-8 py-8 shadow-[0_10px_30px_rgba(40,34,24,0.05)] backdrop-blur-[10px] dark:border-[#242424] dark:bg-[#151515]/84 dark:shadow-[0_14px_34px_rgba(0,0,0,0.22)]">
              {recoveryState ? (
                <RecoveryKeyPanel
                  title="Store your new Recovery Key"
                  subtitle="Your password has been reset locally. This new key replaces the previous one."
                  recoveryKey={recoveryState.recoveryKey}
                  continueLabel="Return to sign in"
                  confirmationLabel="I understand that this recovery key is the only way to recover access if I forget my password."
                  onContinue={() =>
                    navigate({
                      to: "/login",
                    })
                  }
                />
              ) : (
                <div className="space-y-7">
                  <div className="space-y-2 text-left">
                    <h1 className="text-4xl font-medium tracking-tight text-foreground">Recover access</h1>
                    <p className="max-w-2xl text-base text-muted-foreground">
                      Reset your local PrismaLab password using your Recovery Key. Email-based recovery is not available.
                    </p>
                  </div>

                  <form onSubmit={handleSubmit} className="space-y-4">
                    {error && (
                      <div className="rounded-xl border border-destructive/25 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                        {error}
                      </div>
                    )}

                    <div className="space-y-2.5">
                      <Label htmlFor="recover-username" className="text-xs font-medium uppercase tracking-[0.28em] text-muted-foreground">
                        Account
                      </Label>
                      <select
                        id="recover-username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        className="flex h-14 w-full rounded-xl border border-border/80 bg-card/70 px-4 text-base shadow-none focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                        required
                      >
                        {profiles.length === 0 ? (
                          <option value="">No local accounts available</option>
                        ) : (
                          profiles.map((profile) => (
                            <option key={profile.username} value={profile.username}>
                              {profile.fullName}
                            </option>
                          ))
                        )}
                      </select>
                    </div>

                    <div className="space-y-2.5">
                      <Label htmlFor="recovery-key" className="text-xs font-medium uppercase tracking-[0.28em] text-muted-foreground">
                        Recovery Key
                      </Label>
                      <Input
                        id="recovery-key"
                        value={recoveryKey}
                        onChange={(e) => setRecoveryKey(e.target.value.toUpperCase())}
                        placeholder="PLAB-XXXX-XXXX-XXXX-XXXX-XXXX"
                        className="h-14 rounded-xl border-border/80 bg-card/70 px-4 font-mono text-sm tracking-[0.14em] shadow-none sm:text-base"
                        required
                      />
                    </div>

                    <PasswordField
                      id="recover-password"
                      label="New password"
                      value={newPassword}
                      onChange={setNewPassword}
                      placeholder="Create a new password"
                      autoComplete="new-password"
                      required
                    />

                    <PasswordField
                      id="recover-confirm-password"
                      label="Confirm new password"
                      value={confirmPassword}
                      onChange={setConfirmPassword}
                      placeholder="Repeat the new password"
                      autoComplete="new-password"
                      required
                    />

                    <Button
                      type="submit"
                      disabled={isSubmitting || profiles.length === 0}
                      className="mt-2 h-14 w-full rounded-xl border border-border bg-transparent text-lg font-medium text-foreground hover:bg-card/80 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {isSubmitting ? "Recovering access..." : "Reset password"}
                    </Button>
                  </form>

                  <div className="pt-1 text-center">
                    <p className="text-base text-muted-foreground">
                      Ready to sign in?{" "}
                      <Link to="/login" className="font-medium text-brand hover:text-brand-deep transition-colors">
                        Return to access page
                      </Link>
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
