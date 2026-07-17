import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { AssessmentWizard } from "../components/AssessmentWizard";
import { Sidebar } from "../components/Sidebar";

export function DashboardPage() {
  const { user, logout, refresh } = useAuth();
  const [testKey, setTestKey] = useState(0);

  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <Sidebar
        babyName={user?.baby_name}
        ageLabel={user?.age_label}
        onLogout={logout}
      />
      <main className="flex min-h-0 flex-1 flex-col md:min-h-screen">
        <div className="flex-1 overflow-hidden">
          <header className="border-b border-slate-200 bg-white px-4 py-3 md:px-6">
            <h2 className="font-semibold">Шкала Гриффитс</h2>
          </header>
          <div className="overflow-y-auto p-4 md:p-6">
            <AssessmentWizard
              key={testKey}
              babyBirthday={user?.baby_birthday}
              onComplete={async () => {
                await refresh();
                setTestKey((k) => k + 1);
              }}
              onSkip={() => setTestKey((k) => k + 1)}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
