import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { AssessmentWizard } from "../components/AssessmentWizard";
import { ChatWindow } from "../components/ChatWindow";
import { GamePanel } from "../components/GamePanel";
import { OnboardingForm } from "../components/OnboardingForm";
import { ProgressPanel } from "../components/ProgressPanel";
import { Sidebar, type Tab } from "../components/Sidebar";
import { api } from "../api/client";

export function DashboardPage() {
  const { user, logout, refresh } = useAuth();
  const [tab, setTab] = useState<Tab>("chat");
  const [testKey, setTestKey] = useState(0);

  const renderContent = () => {
    switch (tab) {
      case "chat":
        return <ChatWindow />;
      case "game":
        return (
          <div className="overflow-y-auto p-4 md:p-6">
            <GamePanel />
          </div>
        );
      case "test":
        return (
          <div className="overflow-y-auto p-4 md:p-6">
            <AssessmentWizard
              key={testKey}
              babyBirthday={user?.baby_birthday}
              onComplete={async () => {
          await refresh();
          setTab("progress");
        }}
              onSkip={() => setTab("chat")}
            />
          </div>
        );
      case "progress":
        return (
          <div className="overflow-y-auto p-4 md:p-6">
            <ProgressPanel />
          </div>
        );
      case "profile":
        return (
          <div className="overflow-y-auto p-4 md:p-6">
            <OnboardingForm
              initialName={user?.baby_name}
              initialBirthday={user?.baby_birthday}
              ageLabel={user?.age_label}
              onComplete={async (name, birthday) => {
                await api.saveProfile(name, birthday);
                await refresh();
              }}
            />
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <Sidebar
        active={tab}
        onChange={(t) => {
          if (t === "test") setTestKey((k) => k + 1);
          setTab(t);
        }}
        babyName={user?.baby_name}
        ageLabel={user?.age_label}
        onLogout={logout}
      />
      <main className="flex min-h-0 flex-1 flex-col md:min-h-screen">
        {tab === "chat" ? (
          <div className="flex min-h-[calc(100vh-56px)] flex-1 flex-col md:min-h-screen">
            <header className="hidden border-b border-slate-200 bg-white px-6 py-3 md:block">
              <h2 className="font-semibold">Чат с консультантом</h2>
              <p className="text-xs text-slate-500">Powered by NordRouter</p>
            </header>
            {renderContent()}
          </div>
        ) : (
          <div className="flex-1 overflow-hidden">
            <header className="border-b border-slate-200 bg-white px-4 py-3 md:px-6">
              <h2 className="font-semibold">
                {tab === "game" && "Игра на сегодня"}
                {tab === "test" && "Шкала Гриффитс"}
                {tab === "progress" && "Прогресс ребёнка"}
                {tab === "profile" && "Данные ребёнка"}
              </h2>
            </header>
            {renderContent()}
          </div>
        )}
      </main>
    </div>
  );
}
