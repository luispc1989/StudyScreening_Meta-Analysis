import { History, Plus, Send, Trash2, X } from "lucide-react";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { RayAvatar } from "@/components/RayLogo";

export interface RayMessage {
  role: "assistant" | "user";
  content: string;
}

export interface RayConversationSummary {
  id: string;
  title: string;
  messageCount: number;
}

export function RayAssistant({
  onClose,
  messages,
  isThinking,
  onSendMessage,
  onHeaderMouseDown,
  conversations,
  activeConversationId,
  onSelectConversation,
  onCreateConversation,
  onDeleteConversations,
}: {
  onClose: () => void;
  messages: RayMessage[];
  isThinking: boolean;
  onSendMessage: (message: string) => void;
  onHeaderMouseDown: (event: React.MouseEvent<HTMLDivElement>) => void;
  conversations: RayConversationSummary[];
  activeConversationId: string;
  onSelectConversation: (conversationId: string) => void;
  onCreateConversation: () => void;
  onDeleteConversations: (conversationIds: string[]) => void;
}) {
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const historyMenuRef = useRef<HTMLDivElement | null>(null);
  const previousMessageCountRef = useRef(messages.length);
  const [input, setInput] = useState("");
  const [historyOpen, setHistoryOpen] = useState(false);
  const [selectedConversationIds, setSelectedConversationIds] = useState<string[]>([]);
  const [deleteMode, setDeleteMode] = useState(false);

  useLayoutEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "auto", block: "end" });
    previousMessageCountRef.current = messages.length;
  }, []);

  useEffect(() => {
    if (messages.length > previousMessageCountRef.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    }
    previousMessageCountRef.current = messages.length;
  }, [messages]);

  useEffect(() => {
    if (!historyOpen) return;

    const handlePointerDown = (event: MouseEvent) => {
      if (!historyMenuRef.current?.contains(event.target as Node)) {
        setHistoryOpen(false);
        setDeleteMode(false);
        setSelectedConversationIds([]);
      }
    };

    document.addEventListener("mousedown", handlePointerDown);
    return () => document.removeEventListener("mousedown", handlePointerDown);
  }, [historyOpen]);

  const handleSend = () => {
    const value = input.trim();
    if (!value) return;
    onSendMessage(value);
    setInput("");
  };

  const toggleConversationSelection = (conversationId: string) => {
    setSelectedConversationIds((current) =>
      current.includes(conversationId)
        ? current.filter((id) => id !== conversationId)
        : [...current, conversationId],
    );
  };

  const handleDeleteSelected = () => {
    if (!selectedConversationIds.length) return;
    onDeleteConversations(selectedConversationIds);
    setSelectedConversationIds([]);
    setDeleteMode(false);
    setHistoryOpen(false);
  };

  const handleDeleteAll = () => {
    if (!conversations.length) return;
    onDeleteConversations(conversations.map((conversation) => conversation.id));
    setSelectedConversationIds([]);
    setDeleteMode(false);
    setHistoryOpen(false);
  };

  const handleDeleteSingle = (conversationId: string) => {
    onDeleteConversations([conversationId]);
  };

  return (
    <div className="flex h-full w-full flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-[-18px_0_40px_rgba(0,0,0,0.08)]">
      <div
        className="relative border-b border-border bg-card px-6 py-5 cursor-move"
        onMouseDown={onHeaderMouseDown}
      >
        <div className="absolute right-4 top-4 flex items-center gap-2">
          <div ref={historyMenuRef} className="relative">
            <button
              type="button"
              onClick={() => {
                setHistoryOpen((open) => !open);
                setDeleteMode(false);
                setSelectedConversationIds([]);
              }}
              onMouseDown={(event) => event.stopPropagation()}
              className="text-muted-foreground transition-colors hover:text-foreground"
              title="Conversation history"
            >
              <History className="h-4 w-4" />
            </button>
            {historyOpen && (
              <div
                className="absolute right-0 top-8 z-20 w-72 rounded-xl border border-border bg-popover p-3 shadow-xl cursor-default"
                onMouseDown={(event) => event.stopPropagation()}
              >
                <div className="mb-3 px-1">
                  <p className="text-sm font-medium text-foreground">Chat history</p>
                  <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                    Reopen previous Ray conversations for this account.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    onCreateConversation();
                    setHistoryOpen(false);
                  }}
                  className="mb-3 flex w-full items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm text-foreground transition-colors hover:bg-accent"
                >
                  <Plus className="h-4 w-4" />
                  <span>New chat</span>
                </button>
                <div className="max-h-72 space-y-1 overflow-y-auto rounded-lg border border-border/70 bg-background/40 p-1">
                  {conversations.map((conversation) => (
                    <div
                      key={conversation.id}
                      className={`flex items-center gap-2 rounded-lg px-2 py-2 transition-colors ${
                        conversation.id === activeConversationId
                          ? "bg-accent text-foreground"
                          : "text-muted-foreground hover:bg-accent hover:text-foreground"
                      }`}
                    >
                      {deleteMode && (
                        <input
                          type="checkbox"
                          checked={selectedConversationIds.includes(conversation.id)}
                          onChange={() => toggleConversationSelection(conversation.id)}
                          className="h-3.5 w-3.5 rounded border-border"
                        />
                      )}
                      <button
                        type="button"
                        onClick={() => {
                          if (!deleteMode) {
                            onSelectConversation(conversation.id);
                            setHistoryOpen(false);
                          }
                        }}
                        className="min-w-0 flex-1 text-left text-sm"
                      >
                        <span className="block truncate">{conversation.title}</span>
                        <span className="mt-0.5 block text-[11px] text-muted-foreground">
                          {conversation.messageCount} messages
                        </span>
                      </button>
                      {!deleteMode && (
                        <button
                          type="button"
                          onClick={() => handleDeleteSingle(conversation.id)}
                          className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-background hover:text-foreground"
                          title="Delete chat"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      )}
                    </div>
                  ))}
                  {!conversations.length && (
                    <div className="rounded-lg px-3 py-4 text-sm text-muted-foreground">
                      No saved conversations yet.
                    </div>
                  )}
                </div>
                <div className="mt-3 border-t border-border pt-3">
                  <p className="mb-2 px-1 text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
                    Delete
                  </p>
                  <div className="flex items-center justify-between gap-2 px-1">
                    <button
                      type="button"
                      onClick={() => {
                        setDeleteMode((current) => !current);
                        setSelectedConversationIds([]);
                      }}
                      className="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      <span>{deleteMode ? "Cancel delete" : "Select chats"}</span>
                    </button>
                    <button
                      type="button"
                      onClick={handleDeleteAll}
                      disabled={!conversations.length}
                      className="rounded-md px-2 py-1 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-foreground disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      Delete all
                    </button>
                  </div>
                  {deleteMode && (
                    <div className="mt-2 flex items-center justify-end px-1">
                      <button
                        type="button"
                        onClick={handleDeleteSelected}
                        disabled={!selectedConversationIds.length}
                        className="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground transition-colors hover:bg-accent hover:text-foreground disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        <span>Delete selected</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-muted-foreground transition-colors hover:text-foreground"
            title="Close Ray"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex items-center gap-4 pr-16">
          <RayAvatar className="h-14 w-14 shrink-0" size="lg" />
          <div className="h-10 w-px shrink-0 bg-black/12 dark:bg-white/8" />
          <div className="flex flex-col justify-center">
            <div className="flex items-center gap-[7px]">
              <span className="text-[2rem] font-medium leading-none tracking-[-0.04em] text-[#1C1C1A] dark:text-white">
                Ray
              </span>
              <span className="h-[6px] w-[6px] rounded-full bg-[#1D9E75] dark:bg-[#5DCAA5]" />
            </div>
            <span className="mt-1 text-[13px] font-normal text-[#888780] dark:text-white/52">
              Research Assistant
            </span>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            {msg.role === "assistant" ? (
              <div className="flex max-w-[92%] items-start gap-3">
                <RayAvatar className="mt-0.5 h-7 w-7 shrink-0 opacity-90" size="sm" />
                <div className="flex flex-col gap-1.5">
                  <span className="text-xs font-medium text-[#555552] dark:text-white/65">Ray</span>
                  <div className="rounded-[4px_12px_12px_12px] border border-[#E8E7E2] bg-[#F4F3EF] px-4 py-[14px] text-[13.5px] leading-[1.7] text-[#1C1C1A] dark:border-transparent dark:bg-[#1E2129] dark:text-white/80">
                    {msg.content}
                  </div>
                </div>
              </div>
            ) : (
              <div className="max-w-[85%] rounded-xl bg-brand-deep px-3.5 py-2.5 text-sm leading-relaxed text-background">
                {msg.content}
              </div>
            )}
          </div>
        ))}
        {isThinking && (
          <div className="flex justify-start">
            <div className="flex max-w-[92%] items-start gap-3">
              <RayAvatar className="mt-0.5 h-7 w-7 shrink-0 opacity-90" size="sm" />
              <div className="flex flex-col gap-1.5">
                <span className="text-xs font-medium text-[#555552] dark:text-white/65">Ray</span>
                <div className="inline-flex rounded-[4px_12px_12px_12px] border border-[#E8E7E2] bg-[#F4F3EF] px-4 py-3 dark:border-[#1F2530] dark:bg-[#222733]">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 animate-[pulse_1.1s_ease-in-out_infinite] rounded-full bg-[#1D9E75]" />
                    <span className="h-2 w-2 animate-[pulse_1.1s_ease-in-out_0.18s_infinite] rounded-full bg-[#3A9A85]" />
                    <span className="h-2 w-2 animate-[pulse_1.1s_ease-in-out_0.36s_infinite] rounded-full bg-[#5DCAA5]" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-border p-3">
        <div className="flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 focus-within:ring-2 focus-within:ring-brand/30">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask Ray anything..."
            className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={!input.trim()}
            className="text-muted-foreground transition-colors hover:text-brand-deep disabled:opacity-30"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
        <p className="mt-2 text-center text-[10px] text-muted-foreground">
          Ray assists - you decide. Suggestions are not final.
        </p>
      </div>
    </div>
  );
}
