import { useTheme } from "./ThemeProvider";
import { Sun, Moon } from "lucide-react";

export function ThemeSwitcher({ compact = false }: { compact?: boolean }) {
  const { theme, setTheme, resolved } = useTheme();
  const options = [
    { value: "light" as const, icon: Sun, label: "Light" },
    { value: "dark" as const, icon: Moon, label: "Dark" },
  ];

  return (
    <div className="flex items-center gap-1 rounded-lg bg-secondary p-1">
      {options.map(({ value, icon: Icon, label }) => (
        (() => {
          const isActive = theme === "system" ? resolved === value : theme === value;
          return (
        <button
          key={value}
          onClick={() => setTheme(value)}
          className={`flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-all duration-200 ${
            isActive
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          }`}
          title={theme === "system" && resolved === value ? `${label} (following system)` : label}
        >
          <Icon className="h-3.5 w-3.5" />
          {!compact && <span>{label}</span>}
        </button>
          );
        })()
      ))}
    </div>
  );
}
