import { Bot, X, Send, Sparkles } from "lucide-react";
import { useState } from "react";

interface Message {
  role: "assistant" | "user";
  content: string;
}

export function RayAssistant({ onClose }: { onClose: () => void }) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hello! I'm Ray, your research assistant. I can help you with your systematic review workflow — from refining your research question to interpreting synthesis results. How can I help?",
    },
  ]);
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;
    const userMsg = input.trim();
    setMessages((m) => [...m, { role: "user", content: userMsg }]);
    setInput("");
    setTimeout(() => {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: "I understand your question. This feature will be fully connected in a future version. For now, I'm here as a conceptual preview of the Ray Research Assistant experience.",
        },
      ]);
    }, 800);
  };

  return (
    <div className="w-88 xl:w-[26rem] border-l border-border bg-card flex flex-col shadow-[-18px_0_40px_rgba(0,0,0,0.08)]">
      {/* Header */}
      <div className="flex items-center justify-between h-14 px-4 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-full bg-brand/20 flex items-center justify-center">
            <Sparkles className="h-4 w-4 text-brand-deep" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-medium leading-none">Ray</span>
            <span className="text-[10px] text-muted-foreground tracking-wider uppercase mt-1">Research Assistant</span>
          </div>
        </div>
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] rounded-xl px-3.5 py-2.5 text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-brand-deep text-background"
                  : "bg-secondary text-foreground"
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
      </div>

      {/* Input */}
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
            onClick={handleSend}
            disabled={!input.trim()}
            className="text-muted-foreground hover:text-brand-deep disabled:opacity-30 transition-colors"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
        <p className="text-[10px] text-muted-foreground mt-2 text-center">
          Ray assists — you decide. Suggestions are not final.
        </p>
      </div>
    </div>
  );
}
