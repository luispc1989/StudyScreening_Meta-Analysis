import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { PrismaLabLogo } from "@/components/PrismaLabLogo";
import { PrismaLabSplash } from "@/components/PrismaLabSplash";
import { ThemeSwitcher } from "@/components/ThemeSwitcher";
import { PasswordField } from "@/components/PasswordField";
import { deleteLocalProfile, getRememberedUser, hasActiveSession, listLocalProfiles, loginUser, setStoredUser, updateLocalProfile, type User } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Sign In - PrismaLab" },
      { name: "description", content: "Sign in to PrismaLab research synthesis platform" },
    ],
  }),
  component: LoginPage,
});

function LoginPage() {
  const navigate = useNavigate();
  const [isHydrated, setIsHydrated] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [devOpen, setDevOpen] = useState(false);
  const [accounts, setAccounts] = useState<User[]>([]);
  const [selectedUsername, setSelectedUsername] = useState("");
  const [devForm, setDevForm] = useState({ fullName: "", email: "", username: "", nextPassword: "" });
  const [devError, setDevError] = useState("");
  const [devMessage, setDevMessage] = useState("");
  const [rememberedUser, setRememberedUser] = useState("");
  const hasLocalAccounts = accounts.length > 0;

  useEffect(() => {
    if (typeof window === "undefined") return;
    const nextRememberedUser = getRememberedUser() || "";
    const nextAccounts = listLocalProfiles();

    setRememberedUser(nextRememberedUser);
    setUsername(nextRememberedUser);
    setRemember(!!nextRememberedUser);
    setAccounts(nextAccounts);
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!isHydrated) return;
    if (hasActiveSession()) {
      navigate({ to: "/app/dashboard" });
    }
  }, [isHydrated, navigate]);

  useEffect(() => {
    if (!selectedUsername && accounts.length > 0) {
      const first = accounts[0];
      setSelectedUsername(first.username);
      setDevForm({ fullName: first.fullName, email: first.email, username: first.username, nextPassword: "" });
    }
  }, [accounts, selectedUsername]);

  useEffect(() => {
    if (!hasLocalAccounts) return;

    const preferredUsername =
      (rememberedUser && accounts.some((account) => account.username === rememberedUser) && rememberedUser) ||
      (username && accounts.some((account) => account.username === username) && username) ||
      accounts[0]?.username ||
      "";

    if (preferredUsername && preferredUsername !== username) {
      setUsername(preferredUsername);
    }
  }, [hasLocalAccounts, accounts, rememberedUser, username]);

  const refreshAccounts = () => {
    const nextAccounts = listLocalProfiles();
    setAccounts(nextAccounts);
    return nextAccounts;
  };

  const hydrateSelectedProfile = (value: string) => {
    setSelectedUsername(value);
    const account = accounts.find((item) => item.username === value);
    if (!account) {
      setDevForm({ fullName: "", email: "", username: "", nextPassword: "" });
      return;
    }
    setDevForm({
      fullName: account.fullName,
      email: account.email,
      username: account.username,
      nextPassword: "",
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;
    setError("");

    if (!username.trim() || !password.trim()) {
      setError("Enter both username and password to continue");
      return;
    }

    setIsSubmitting(true);
    window.setTimeout(async () => {
      const user = await loginUser(username, password);
      if (!user) {
        setError("Invalid username or password");
        setIsSubmitting(false);
        return;
      }
      setStoredUser(user, remember);
      navigate({ to: "/app/dashboard" });
    }, 900);
  };

  const handleDevAccess = () => {
    const devAccount =
      accounts.find((account) => account.username === "luispc1989") ?? {
        fullName: "Luis Pinto Coelho",
        email: "luispc1989@prismalab.local",
        username: "luispc1989",
      };

    setStoredUser(
      devAccount,
      true,
    );
    navigate({ to: "/app/dashboard" });
  };

  const handleDevSave = async () => {
    if (!selectedUsername) return;
    setDevError("");
    setDevMessage("");
    if (!devForm.fullName.trim() || !devForm.email.trim() || !devForm.username.trim()) {
      setDevError("Complete full name, email, and username before saving");
      return;
    }
    if (devForm.nextPassword && devForm.nextPassword.length < 8) {
      setDevError("New password must be at least 8 characters");
      return;
    }

    try {
      await updateLocalProfile({
        currentUsername: selectedUsername,
        fullName: devForm.fullName,
        email: devForm.email,
        username: devForm.username,
        nextPassword: devForm.nextPassword || undefined,
      });
      const nextAccounts = refreshAccounts();
      const savedUsername = devForm.username.trim();
      setSelectedUsername(savedUsername);
      const savedAccount = nextAccounts.find((item) => item.username === savedUsername);
      if (savedAccount) {
        setDevForm({
          fullName: savedAccount.fullName,
          email: savedAccount.email,
          username: savedAccount.username,
          nextPassword: "",
        });
      }
      setDevMessage("Account updated");
    } catch (err) {
      setDevError(err instanceof Error ? err.message : "Could not update account");
    }
  };

  const handleDevDelete = async () => {
    if (!selectedUsername) return;
    setDevError("");
    setDevMessage("");
    try {
      await deleteLocalProfile(selectedUsername);
      const nextAccounts = refreshAccounts();
      if (nextAccounts.length > 0) {
        hydrateSelectedProfile(nextAccounts[0].username);
      } else {
        setSelectedUsername("");
        setDevForm({ fullName: "", email: "", username: "", nextPassword: "" });
      }
      setDevMessage("Account removed");
    } catch (err) {
      setDevError(err instanceof Error ? err.message : "Could not remove account");
    }
  };

  if (!isHydrated) {
    return <PrismaLabSplash label="Loading access page" />;
  }

  if (isSubmitting) {
    return <PrismaLabSplash label="Signing in" />;
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-background text-foreground">
      <div className="absolute inset-0 bg-white dark:bg-[#111111]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(93,202,165,0.05),transparent_30%),radial-gradient(circle_at_bottom,rgba(55,138,221,0.04),transparent_24%)] dark:bg-[radial-gradient(circle_at_top,rgba(93,202,165,0.07),transparent_30%),radial-gradient(circle_at_bottom,rgba(55,138,221,0.06),transparent_24%)]" />
      <div className="absolute inset-3 rounded-[2rem] border border-[#e7e2d8] bg-white/98 shadow-[0_18px_50px_rgba(40,34,24,0.05)] dark:border-[#1c1c1a] dark:bg-[#111111]/98 dark:shadow-[0_24px_80px_rgba(0,0,0,0.28)]" />
      <div className="pointer-events-none absolute left-1/2 top-[54%] h-[30rem] w-[42rem] -translate-x-1/2 -translate-y-1/2 rounded-[3rem] bg-[radial-gradient(circle,rgba(255,255,255,0.72)_0%,rgba(255,255,255,0.36)_48%,transparent_80%)] blur-3xl dark:bg-[radial-gradient(circle,rgba(26,26,26,0.42)_0%,rgba(17,17,17,0.12)_52%,transparent_82%)]" />

      <div className="relative flex min-h-screen flex-col">
        <div className="flex items-center justify-end px-4 pt-4 pb-2 sm:px-6 sm:pt-5 sm:pb-3">
          <ThemeSwitcher compact />
        </div>

        <div className="flex flex-1 items-start justify-center px-4 pb-8 pt-3 sm:px-6 sm:pb-10 sm:pt-4 lg:pb-12 xl:pt-5">
          <div className="grid w-full max-w-[78rem] justify-items-center">
            <div className="mx-auto flex w-full justify-center text-center">
              <PrismaLabLogo
                showTagline
                size="lg"
                tone="auto"
                className="w-full max-w-[22rem] sm:max-w-[28rem] md:max-w-[34rem] lg:max-w-[40rem] xl:max-w-[48rem] 2xl:max-w-[54rem]"
              />
            </div>

            <div className="relative mx-auto mt-4 w-full max-w-[28rem] rounded-[1.5rem] border border-[#e7ded0] bg-white/88 px-5 py-6 shadow-[0_16px_36px_rgba(40,34,24,0.06)] backdrop-blur-[10px] sm:mt-5 sm:max-w-[30rem] sm:px-7 sm:py-7 lg:max-w-[31rem] xl:mt-6 xl:max-w-[32rem] 2xl:max-w-[33rem] dark:border-[#242424] dark:bg-[#151515]/88 dark:shadow-[0_16px_36px_rgba(0,0,0,0.24)]">
              <div className="space-y-8">
                <div className="space-y-2 text-center">
                  <h1 className="text-[1.7rem] font-medium tracking-tight leading-[1] text-foreground sm:text-[1.95rem] md:text-[2.2rem] xl:text-[2.35rem]">
                    {rememberedUser ? (
                      "Welcome back"
                    ) : (
                      <span className="inline-flex items-baseline gap-[0.18em]">
                        <span>Access</span>
                        <span className="inline-flex items-baseline tracking-tight">
                          <span>Prisma</span>
                          <span className="ml-[0.08em]">Lab</span>
                        </span>
                      </span>
                    )}
                  </h1>
                  <p className="text-base text-muted-foreground sm:text-[1.05rem]">
                    {rememberedUser ? "Sign in to continue your research" : "Sign in or create your local research workspace"}
                  </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                  {error && (
                    <div className="rounded-xl border border-destructive/25 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                      {error}
                    </div>
                  )}

                  {hasLocalAccounts ? (
                    <div className="space-y-2.5">
                      <Label htmlFor="account" className="text-xs font-medium uppercase tracking-[0.28em] text-muted-foreground">
                        Account
                      </Label>
                      <select
                        id="account"
                        value={username}
                        onChange={(e) => {
                          setUsername(e.target.value);
                          setError("");
                        }}
                        className="flex h-14 w-full rounded-xl border border-border/80 bg-card/70 px-4 text-base shadow-none focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                        required
                      >
                        {accounts.map((account) => (
                          <option key={account.username} value={account.username}>
                            {account.fullName}
                          </option>
                        ))}
                      </select>
                    </div>
                  ) : (
                    <div className="space-y-2.5">
                      <Label htmlFor="username" className="text-xs font-medium uppercase tracking-[0.28em] text-muted-foreground">
                        Username
                      </Label>
                      <Input
                        id="username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder="Enter your username"
                        autoComplete="username"
                        className="h-14 rounded-xl border-border/80 bg-card/70 px-4 text-base shadow-none"
                        required
                      />
                    </div>
                  )}

                  <PasswordField
                    id="password"
                    label="Password"
                    value={password}
                    onChange={setPassword}
                    placeholder="Enter your password"
                    autoComplete="current-password"
                    required
                  />

                  <div className="flex items-center gap-3 pt-1">
                    <input
                      type="checkbox"
                      id="remember"
                      checked={remember}
                      onChange={(e) => setRemember(e.target.checked)}
                      className="h-4 w-4 rounded border-border bg-background accent-[var(--color-brand-deep)]"
                    />
                    <Label htmlFor="remember" className="cursor-pointer text-base text-muted-foreground">
                      Remember me
                    </Label>
                  </div>

                  <Button
                    type="submit"
                    disabled={isSubmitting}
                    className="h-14 w-full rounded-xl border border-brand/70 bg-brand text-xl font-medium text-primary-foreground shadow-[0_10px_24px_rgba(93,202,165,0.16)] transition-colors hover:bg-brand-deep hover:border-brand-deep disabled:cursor-not-allowed disabled:opacity-60 dark:shadow-[0_10px_24px_rgba(93,202,165,0.12)]"
                  >
                    {isSubmitting ? "Signing in..." : "Sign in"}
                  </Button>
                </form>

                <div className="space-y-3 pt-2 text-center">
                  <p className="text-base text-muted-foreground">
                    Don't have an account?{" "}
                    <Link to="/register" className="font-medium text-brand hover:text-brand-deep transition-colors">
                      Create account
                    </Link>
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Need to reset your local password?{" "}
                    <Link to="/recover" className="font-medium text-brand hover:text-brand-deep transition-colors">
                      Recover access
                    </Link>
                  </p>
                  <button
                    type="button"
                    onClick={handleDevAccess}
                    className="inline-flex items-center justify-center rounded-lg border border-dashed border-border px-3 py-1.5 text-xs font-medium tracking-[0.22em] text-muted-foreground transition-colors hover:border-brand/40 hover:text-brand-deep"
                  >
                    DEV
                  </button>
                  <button
                    type="button"
                    onClick={() => setDevOpen((current) => !current)}
                    className="ml-2 inline-flex items-center justify-center rounded-lg border border-dashed border-border px-3 py-1.5 text-xs font-medium tracking-[0.18em] text-muted-foreground transition-colors hover:border-brand/40 hover:text-brand-deep"
                  >
                    {devOpen ? "Hide DEV menu" : "Open DEV menu"}
                  </button>
                </div>

                {devOpen ? (
                  <div className="space-y-4 rounded-2xl border border-dashed border-border/80 bg-background/70 p-4 text-left">
                    <div className="space-y-1">
                      <p className="text-xs font-medium uppercase tracking-[0.28em] text-muted-foreground">DEV Menu</p>
                      <p className="text-sm text-muted-foreground">Temporary local account inspector and editor.</p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="dev-profile" className="text-xs font-medium uppercase tracking-[0.28em] text-muted-foreground">
                        Local accounts
                      </Label>
                      <select
                        id="dev-profile"
                        value={selectedUsername}
                        onChange={(e) => hydrateSelectedProfile(e.target.value)}
                        className="flex h-12 w-full rounded-xl border border-border/80 bg-card/70 px-4 text-sm shadow-none focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                      >
                        {accounts.length === 0 ? (
                          <option value="">No local accounts</option>
                        ) : (
                          accounts.map((account) => (
                            <option key={account.username} value={account.username}>
                              {account.username} ({account.email})
                            </option>
                          ))
                        )}
                      </select>
                    </div>

                    <div className="grid gap-3">
                      <div className="space-y-2">
                        <Label htmlFor="dev-fullname" className="text-xs font-medium uppercase tracking-[0.28em] text-muted-foreground">
                          Full name
                        </Label>
                        <Input
                          id="dev-fullname"
                          value={devForm.fullName}
                          onChange={(e) => setDevForm((current) => ({ ...current, fullName: e.target.value }))}
                          className="h-12 rounded-xl border-border/80 bg-card/70 px-4 text-sm shadow-none"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="dev-email" className="text-xs font-medium uppercase tracking-[0.28em] text-muted-foreground">
                          Email
                        </Label>
                        <Input
                          id="dev-email"
                          value={devForm.email}
                          onChange={(e) => setDevForm((current) => ({ ...current, email: e.target.value }))}
                          className="h-12 rounded-xl border-border/80 bg-card/70 px-4 text-sm shadow-none"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="dev-username" className="text-xs font-medium uppercase tracking-[0.28em] text-muted-foreground">
                          Username
                        </Label>
                        <Input
                          id="dev-username"
                          value={devForm.username}
                          onChange={(e) => setDevForm((current) => ({ ...current, username: e.target.value }))}
                          className="h-12 rounded-xl border-border/80 bg-card/70 px-4 text-sm shadow-none"
                        />
                      </div>
                      <PasswordField
                        id="dev-password-reset"
                        label="Set new password"
                        value={devForm.nextPassword}
                        onChange={(value) => setDevForm((current) => ({ ...current, nextPassword: value }))}
                        placeholder="Leave empty to keep current password"
                      />
                    </div>

                    {devError ? (
                      <div className="rounded-xl border border-destructive/25 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                        {devError}
                      </div>
                    ) : null}

                    {devMessage ? (
                      <div className="rounded-xl border border-brand/20 bg-brand/10 px-4 py-3 text-sm text-brand-deep dark:text-brand">
                        {devMessage}
                      </div>
                    ) : null}

                    <div className="flex flex-col gap-3 sm:flex-row">
                      <Button
                        type="button"
                        variant="outline"
                        className="h-12 flex-1 rounded-xl text-sm"
                        onClick={handleDevSave}
                        disabled={!selectedUsername}
                      >
                        Save changes
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        className="h-12 flex-1 rounded-xl border-destructive/30 text-sm text-destructive hover:bg-destructive/10 hover:text-destructive"
                        onClick={handleDevDelete}
                        disabled={!selectedUsername}
                      >
                        Remove account
                      </Button>
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
