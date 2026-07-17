interface Props {
  babyName?: string;
  ageLabel?: string;
  onLogout: () => void;
}

export function Sidebar({ babyName, ageLabel, onLogout }: Props) {
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
      <div className="flex-1" />
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
