type Tab = "chat" | "game" | "test" | "progress" | "profile";

interface Props {
  active: Tab;
  onChange: (tab: Tab) => void;
  babyName?: string;
  ageLabel?: string;
  onLogout: () => void;
}

const items: { id: Tab; label: string; icon: string }[] = [
  { id: "chat", label: "Чат", icon: "💬" },
  { id: "game", label: "Игра на сегодня", icon: "🎮" },
  { id: "test", label: "Шкала Гриффитс", icon: "📋" },
  { id: "progress", label: "Прогресс", icon: "📈" },
  { id: "profile", label: "Профиль", icon: "✏️" },
];

export function Sidebar({ active, onChange, babyName, ageLabel, onLogout }: Props) {
  return (
    <aside className="flex w-full flex-col border-r border-slate-200 bg-white md:w-64 md:min-h-screen">
      <div className="border-b border-slate-200 p-4">
        <h1 className="text-lg font-bold text-brand-700">Гриффитс</h1>
        <p className="text-xs text-slate-500">Нейроконсультант 0–2 года</p>
        {babyName && (
          <div className="mt-3 rounded-xl bg-brand-50 px-3 py-2 text-sm">
            <p className="font-medium">{babyName}</p>
            {ageLabel && <p className="text-slate-500">{ageLabel}</p>}
          </div>
        )}
      </div>
      <nav className="flex flex-1 gap-1 overflow-x-auto p-2 md:flex-col md:overflow-visible">
        {items.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => onChange(item.id)}
            className={`flex shrink-0 items-center gap-2 rounded-xl px-3 py-2.5 text-left text-sm transition md:w-full ${
              active === item.id
                ? "bg-brand-600 text-white"
                : "text-slate-700 hover:bg-slate-100"
            }`}
          >
            <span>{item.icon}</span>
            <span className="whitespace-nowrap">{item.label}</span>
          </button>
        ))}
      </nav>
      <div className="border-t border-slate-200 p-3">
        <button
          type="button"
          onClick={onLogout}
          className="w-full rounded-xl px-3 py-2 text-sm text-slate-500 hover:bg-slate-100"
        >
          Выйти
        </button>
      </div>
    </aside>
  );
}

export type { Tab };
