import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { AssessmentWizard } from "../components/AssessmentWizard";
import { ChatWindow } from "../components/ChatWindow";
import { GamePanel } from "../components/GamePanel";
import { OnboardingForm } from "../components/OnboardingForm";
import { ProgressPanel } from "../components/ProgressPanel";
import { Sidebar, type Tab } from "../components/Sidebar";
import { api } from "../api/client";

function readPaymentParams() {
  const params = new URLSearchParams(window.location.search);
  return {
    tab: params.get("tab"),
    returnFromPayment: params.get("from_payment") === "1",
    paymentId: params.get("payment_id") ?? undefined,
  };
}

export function DashboardPage() {
  const { user, logout, refresh } = useAuth();
  const initial = readPaymentParams();
  const [tab, setTab] = useState<Tab>(
    initial.tab === "game" ? "game" : "chat"
  );
  const [returnFromPayment, setReturnFromPayment] = useState(
    initial.returnFromPayment
  );
  const [paymentId, setPaymentId] = useState<string | undefined>(
    initial.paymentId
  );
  const [testKey, setTestKey] = useState(0);

  useEffect(() => {
    const { tab: tabParam, returnFromPayment: fromPayment, paymentId: pid } =
      readPaymentParams();
    if (tabParam === "game") setTab("game");
    if (fromPayment) setReturnFromPayment(true);
    if (pid) setPaymentId(pid);

    if (tabParam || fromPayment || pid) {
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, []);

  const renderContent = () => {
    switch (tab) {
      case "chat":
        return <ChatWindow />;
      case "game":
        return (
          <div className="overflow-y-auto p-4 md:p-6">
            <GamePanel
              returnFromPayment={returnFromPayment}
              paymentId={paymentId}
            />
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
