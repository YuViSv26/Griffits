import { useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { AssessmentWizard } from "../components/AssessmentWizard";
import { OnboardingForm } from "../components/OnboardingForm";

type Step = "profile" | "test-offer" | "test";

export function OnboardingPage() {
  const { refresh } = useAuth();
  const [step, setStep] = useState<Step>("profile");
  const [savedBirthday, setSavedBirthday] = useState("");

  const finishOnboarding = async () => {
    await refresh();
  };

  const handleProfile = async (name: string, birthday: string) => {
    await api.saveProfile(name, birthday);
    setSavedBirthday(birthday);
    setStep("test-offer");
  };

  if (step === "profile") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
        <OnboardingForm onComplete={handleProfile} />
      </div>
    );
  }

  if (step === "test-offer") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
        <div className="mx-auto max-w-md rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm">
          <h2 className="text-xl font-semibold">Оценка развития</h2>
          <p className="mt-2 text-sm text-slate-500">
            Адаптивный опрос по шкале Гриффитс (Кешишян, 0–2 года). Подберём игры
            под уровень малыша.
          </p>
          <div className="mt-6 flex flex-col gap-3">
            <button
              type="button"
              onClick={() => setStep("test")}
              className="rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-brand-700"
            >
              Пройти тест
            </button>
            <button
              type="button"
              onClick={finishOnboarding}
              className="text-sm text-slate-500 hover:text-slate-700"
            >
              Пропустить
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
      <AssessmentWizard
        babyBirthday={savedBirthday}
        onComplete={finishOnboarding}
        onSkip={finishOnboarding}
      />
    </div>
  );
}
