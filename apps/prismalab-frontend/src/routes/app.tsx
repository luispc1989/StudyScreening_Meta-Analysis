import { createFileRoute, Outlet, Link, useLocation, useNavigate } from "@tanstack/react-router";
import { useEffect, useMemo, useRef, useState } from "react";
import { PrismaLabLogo, PrismaLabMark } from "@/components/PrismaLabLogo";
import { PrismaLabSplash } from "@/components/PrismaLabSplash";
import { ThemeSwitcher } from "@/components/ThemeSwitcher";
import { RayAssistant, type RayConversationSummary, type RayMessage } from "@/components/RayAssistant";
import { RayAvatar } from "@/components/RayLogo";
import { getStoredUser, hasActiveSession, logout, touchActiveSession } from "@/lib/auth";
import { WorkspaceHomePage } from "@/routes/app.dashboard";
import {
  FileQuestion, Search, FileCheck, ShieldCheck, Database,
  BarChart3, MessageSquareText, Settings, LogOut, PanelLeft,
  ChevronRight, House,
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

interface RayConversation {
  id: string;
  title: string;
  messages: RayMessage[];
}

const starterMessage: RayMessage = {
  role: "assistant",
  content:
    "Hello! I'm Ray, your research assistant. I can help you with your systematic review workflow - from refining your research question to interpreting synthesis results. How can I help?",
};

const DEFAULT_RAY_WIDTH = 432;
const DEFAULT_RAY_HEIGHT = 576;
const DEFAULT_RAY_MARGIN = 16;

function createEmptyRayConversation(id = `conversation-${Date.now()}`): RayConversation {
  return { id, title: "New chat", messages: [starterMessage] };
}

function getRayHistoryStorageKey(username: string) {
  return `prismalab-ray-history:${username}`;
}

function AppShell() {
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);
  const [rayOpen, setRayOpen] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [isRayThinking, setIsRayThinking] = useState(false);
  const [rayRect, setRayRect] = useState({ left: 0, top: 0 });
  const [rayConversations, setRayConversations] = useState<RayConversation[]>([createEmptyRayConversation("conversation-1")]);
  const [activeConversationId, setActiveConversationId] = useState("conversation-1");
  const [rayHistoryReady, setRayHistoryReady] = useState(false);
  const location = useLocation();
  const user = getStoredUser();
  const dragRef = useRef<{ offsetX: number; offsetY: number } | null>(null);
  const workspaceRef = useRef<HTMLDivElement | null>(null);

  const isActive = (path: string) => location.pathname.includes(path);
  const showWorkspaceHome = location.pathname === "/app" || location.pathname === "/app/";
  const activeConversation =
    rayConversations.find((conversation) => conversation.id === activeConversationId) ?? rayConversations[0];
  const conversationSummaries = useMemo<RayConversationSummary[]>(
    () =>
      rayConversations
        .filter((conversation) => conversation.messages.some((message) => message.role === "user"))
        .map(({ id, title, messages }) => ({ id, title, messageCount: messages.length })),
    [rayConversations],
  );

  const positionRayPanel = () => {
    const workspace = workspaceRef.current;
    if (!workspace) return;

    const left = Math.max(DEFAULT_RAY_MARGIN, workspace.clientWidth - DEFAULT_RAY_WIDTH - DEFAULT_RAY_MARGIN);
    const top = Math.max(
      DEFAULT_RAY_MARGIN,
      Math.min(32, workspace.clientHeight - DEFAULT_RAY_HEIGHT - DEFAULT_RAY_MARGIN),
    );
    setRayRect({ left, top });
  };

  useEffect(() => {
    if (!hasActiveSession()) {
      window.location.href = "/login";
      return;
    }

    touchActiveSession();

    const interval = window.setInterval(() => {
      touchActiveSession();
    }, 30000);

    const handleVisibility = () => {
      if (document.visibilityState === "visible") {
        touchActiveSession();
      }
    };

    window.addEventListener("focus", touchActiveSession);
    document.addEventListener("visibilitychange", handleVisibility);

    return () => {
      window.clearInterval(interval);
      window.removeEventListener("focus", touchActiveSession);
      document.removeEventListener("visibilitychange", handleVisibility);
    };
  }, []);

  useEffect(() => {
    if (!user?.username) {
      setRayHistoryReady(false);
      return;
    }

    const storageKey = getRayHistoryStorageKey(user.username);
    setRayHistoryReady(false);

    try {
      const raw = localStorage.getItem(storageKey);
      if (!raw) {
        const fallback = createEmptyRayConversation("conversation-1");
        setRayConversations([fallback]);
        setActiveConversationId(fallback.id);
        setRayHistoryReady(true);
        return;
      }

      const parsed = JSON.parse(raw) as {
        conversations?: RayConversation[];
        activeConversationId?: string;
      };

      const conversations =
        parsed.conversations && parsed.conversations.length
          ? parsed.conversations
          : [createEmptyRayConversation("conversation-1")];

      const nextActiveId =
        parsed.activeConversationId && conversations.some((conversation) => conversation.id === parsed.activeConversationId)
          ? parsed.activeConversationId
          : conversations[0].id;

      setRayConversations(conversations);
      setActiveConversationId(nextActiveId);
      setRayHistoryReady(true);
    } catch {
      const fallback = createEmptyRayConversation("conversation-1");
      setRayConversations([fallback]);
      setActiveConversationId(fallback.id);
      setRayHistoryReady(true);
    }
  }, [user?.username]);

  useEffect(() => {
    if (!user?.username || !rayHistoryReady) return;

    const storageKey = getRayHistoryStorageKey(user.username);
    localStorage.setItem(
      storageKey,
      JSON.stringify({
        conversations: rayConversations,
        activeConversationId,
      }),
    );
  }, [activeConversationId, rayConversations, rayHistoryReady, user?.username]);

  useEffect(() => {
    positionRayPanel();
    window.addEventListener("resize", positionRayPanel);
    return () => window.removeEventListener("resize", positionRayPanel);
  }, []);

  useEffect(() => {
    if (!rayOpen) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setRayOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [rayOpen]);

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      if (!dragRef.current) return;

      const margin = 8;
      const workspace = workspaceRef.current;
      if (!workspace) return;
      const panel = document.getElementById("ray-panel");
      const width = panel?.offsetWidth ?? 432;
      const height = panel?.offsetHeight ?? 560;
      const workspaceRect = workspace.getBoundingClientRect();
      const nextLeft = Math.min(
        Math.max(margin, event.clientX - workspaceRect.left - dragRef.current.offsetX),
        workspace.clientWidth - width - margin,
      );
      const nextTop = Math.min(
        Math.max(margin, event.clientY - workspaceRect.top - dragRef.current.offsetY),
        workspace.clientHeight - height - margin,
      );
      setRayRect({ left: nextLeft, top: nextTop });
    };

    const handleMouseUp = () => {
      dragRef.current = null;
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, []);

  const handleLogout = () => {
    if (isLoggingOut) return;
    setIsLoggingOut(true);
    window.setTimeout(() => {
      logout();
      navigate({ to: "/login" });
    }, 450);
  };

  const handleRayHeaderMouseDown = (event: React.MouseEvent<HTMLDivElement>) => {
    if ((event.target as HTMLElement).closest("button")) return;
    const panel = document.getElementById("ray-panel");
    if (!panel) return;
    const panelRect = panel.getBoundingClientRect();
    dragRef.current = {
      offsetX: event.clientX - panelRect.left,
      offsetY: event.clientY - panelRect.top,
    };
  };

  const handleRaySendMessage = (message: string) => {
    setIsRayThinking(true);
    setRayConversations((conversations) =>
      conversations.map((conversation) =>
        conversation.id === activeConversationId
          ? {
              ...conversation,
              title:
                conversation.title === "New chat" ? message.slice(0, 36) || "New chat" : conversation.title,
              messages: [...conversation.messages, { role: "user", content: message }],
            }
          : conversation,
      ),
    );

    window.setTimeout(() => {
      setRayConversations((conversations) =>
        conversations.map((conversation) =>
          conversation.id === activeConversationId
            ? {
                ...conversation,
                messages: [
                  ...conversation.messages,
                  {
                    role: "assistant",
                    content:
                      "I understand your question. This feature will be fully connected in a future version. For now, I'm here as a conceptual preview of the Ray Research Assistant experience.",
                  },
                ],
              }
            : conversation,
        ),
      );
      setIsRayThinking(false);
    }, 800);
  };

  const handleCreateConversation = () => {
    const id = `conversation-${Date.now()}`;
    setRayConversations((conversations) => [
      createEmptyRayConversation(id),
      ...conversations,
    ]);
    setActiveConversationId(id);
    return id;
  };

  const handleOpenRay = () => {
    positionRayPanel();
    setRayOpen(true);
  };

  const handleDeleteConversations = (conversationIds: string[]) => {
    if (!conversationIds.length) return;

    setRayConversations((conversations) => {
      const remaining = conversations.filter((conversation) => !conversationIds.includes(conversation.id));
      if (!remaining.length) {
        const fallbackId = `conversation-${Date.now()}`;
        setActiveConversationId(fallbackId);
        return [createEmptyRayConversation(fallbackId)];
      }

      if (conversationIds.includes(activeConversationId)) {
        setActiveConversationId(remaining[0].id);
      }

      return remaining;
    });
  };

  if (isLoggingOut) {
    return <PrismaLabSplash label="Signing out" />;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside
        className={`flex flex-col border-r border-border bg-card transition-all duration-200 ease-out ${
          collapsed ? "w-16" : "w-64"
        }`}
      >
        {/* Logo */}
        <div className={`flex items-center border-b border-border ${collapsed ? "h-16 px-2" : "h-28 px-2.5"}`}>
          {collapsed ? (
            <PrismaLabMark size={44} className="mx-auto" />
          ) : (
            <PrismaLabLogo size="lg" showTagline={false} className="w-full max-w-none" />
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
          {!collapsed && (
            <span className="text-[10px] font-medium tracking-[0.2em] uppercase text-muted-foreground px-2 mb-2 block">
              Workspace
            </span>
          )}
          <Link
            to="/app"
            className={`mb-2 flex items-center gap-3 rounded-lg px-2.5 py-2 text-sm transition-colors duration-120 ${
              showWorkspaceHome
                ? "bg-accent text-foreground font-medium"
                : "text-muted-foreground hover:bg-secondary hover:text-foreground"
            }`}
            title={collapsed ? "Home" : undefined}
          >
            <div className="relative flex-shrink-0">
              <House className="h-4 w-4" />
              <div className={`absolute -left-1 -top-1 h-1.5 w-1.5 rounded-full bg-brand-deep ${showWorkspaceHome ? "opacity-100" : "opacity-40"}`} />
            </div>
            {!collapsed && <span className="truncate">Home</span>}
            {!collapsed && showWorkspaceHome && <ChevronRight className="h-3 w-3 ml-auto opacity-40" />}
          </Link>

          {!collapsed && (
            <span className="text-[10px] font-medium tracking-[0.2em] uppercase text-muted-foreground px-2 mb-2 mt-3 block">
              Workflow
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
                onClick={handleLogout}
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
      <div className="relative flex-1 flex flex-col min-w-0">
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
        <div ref={workspaceRef} className="relative flex-1 overflow-hidden">
          <main className="h-full overflow-y-auto">
            {showWorkspaceHome ? <WorkspaceHomePage /> : <Outlet />}
          </main>

          {/* Ray Assistant Panel */}
          {rayOpen && (
            <div
              id="ray-panel"
              className="absolute z-30 flex min-h-[30rem] min-w-[23rem] max-h-[calc(100vh-1rem)] max-w-[calc(100%-1rem)] resize overflow-hidden"
              style={{ left: rayRect.left, top: rayRect.top, width: "27rem", height: "36rem" }}
            >
              <RayAssistant
                onClose={() => setRayOpen(false)}
                messages={activeConversation.messages}
                isThinking={isRayThinking}
                onSendMessage={handleRaySendMessage}
                onHeaderMouseDown={handleRayHeaderMouseDown}
                conversations={conversationSummaries}
                activeConversationId={activeConversation.id}
                onSelectConversation={setActiveConversationId}
                onCreateConversation={handleCreateConversation}
                onDeleteConversations={handleDeleteConversations}
              />
            </div>
          )}
        </div>

        {!rayOpen && (
          <button
            type="button"
            onClick={handleOpenRay}
            className="absolute bottom-6 right-6 z-30 flex h-16 w-16 items-center justify-center bg-transparent text-foreground transition-transform hover:scale-[1.02]"
            aria-label="Open Ray Research Assistant"
            title="Open Ray Research Assistant"
          >
            <RayAvatar
              size="lg"
              className="h-14 w-14 drop-shadow-[0_10px_24px_rgba(0,0,0,0.16)] dark:drop-shadow-[0_10px_24px_rgba(0,0,0,0.4)]"
            />
          </button>
        )}
      </div>
    </div>
  );
}
