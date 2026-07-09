import { useEffect, useState } from "react";
import { api } from "../api/client";
import { Button, Card, Spinner } from "./ui";

interface Props {
  userEmail?: string;
  returnFromPayment?: boolean;
  paymentId?: string;
  onDone?: () => void;
}

export function PlanPaymentPrompt({
  userEmail,
  returnFromPayment = false,
  paymentId,
  onDone,
}: Props) {
  const [paying, setPaying] = useState(false);
  const [checkingPayment, setCheckingPayment] = useState(false);
  const [paid, setPaid] = useState(false);
  const [pdfEmailed, setPdfEmailed] = useState(false);
  const [priceRub, setPriceRub] = useState(199);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!returnFromPayment && !paymentId) return;

    let cancelled = false;

    async function verifyPayment() {
      setCheckingPayment(true);
      for (let attempt = 0; attempt < 5 && !cancelled; attempt++) {
        try {
          const status = paymentId
            ? await api.getPlanPdfPaymentStatus(paymentId)
            : await api.getLatestPlanPdfPaymentStatus();
          if (cancelled) return;

          setPriceRub(status.amount_rub);

          if (status.paid) {
            setPaid(true);
            setPdfEmailed(status.pdf_emailed);
            break;
          }

          if (status.status === "canceled") {
            setError("Оплата отменена. Попробуйте снова.");
            break;
          }
        } catch (e) {
          if (attempt === 4 && !cancelled) {
            setError(
              e instanceof Error
                ? e.message
                : "Не удалось проверить статус оплаты"
            );
          }
        }

        if (attempt < 4) {
          await new Promise((resolve) => setTimeout(resolve, 2000));
        }
      }
      if (!cancelled) setCheckingPayment(false);
    }

    verifyPayment();
    return () => {
      cancelled = true;
    };
  }, [returnFromPayment, paymentId]);

  const handlePay = async () => {
    setPaying(true);
    setError("");
    try {
      const res = await api.createPlanPdfPayment("test");
      setPriceRub(res.amount_rub);
      window.location.href = res.confirmation_url;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось создать платёж");
      setPaying(false);
    }
  };

  if (checkingPayment) {
    return (
      <Card className="flex items-center gap-3 border-brand-100 bg-brand-50/50 p-4 text-sm text-brand-800">
        <Spinner />
        Проверяем оплату…
      </Card>
    );
  }

  if (paid) {
    return (
      <Card className="border-emerald-100 bg-emerald-50/60 p-6">
        <h3 className="text-lg font-semibold text-emerald-900">
          Оплата прошла успешно
        </h3>
        {pdfEmailed ? (
          <p className="mt-2 text-sm text-emerald-800">
            Персональный план в формате PDF отправлен на{" "}
            <strong>{userEmail ?? "вашу почту"}</strong>. Проверьте входящие и
            папку «Спам».
          </p>
        ) : (
          <p className="mt-2 text-sm text-emerald-800">
            Оплата принята. PDF-план будет отправлен на{" "}
            <strong>{userEmail ?? "вашу почту"}</strong> в ближайшие минуты.
          </p>
        )}
        {onDone && (
          <Button className="mt-4 bg-brand-600 hover:bg-brand-700" onClick={onDone}>
            Продолжить
          </Button>
        )}
      </Card>
    );
  }

  return (
    <Card className="border-brand-100 bg-brand-50/40 p-6">
      <h3 className="text-lg font-semibold text-brand-900">
        Получить план развития на email
      </h3>
      <p className="mt-2 text-sm text-slate-600">
        После оплаты на вашу почту придёт PDF с персональным планом:
      </p>
      <ul className="mt-3 list-inside list-disc space-y-1 text-sm text-slate-600">
        <li>ориентиры по шкале Гриффитс на текущий возраст</li>
        <li>на что обратить внимание</li>
        <li>игры для развития слабой сферы</li>
        <li>рекомендации по занятиям</li>
        <li>важные напоминания</li>
      </ul>
      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      <Button
        className="mt-4 w-full bg-brand-600 hover:bg-brand-700"
        onClick={handlePay}
        disabled={paying}
      >
        {paying ? <Spinner /> : `Оплатить ${priceRub} ₽ и получить PDF на email`}
      </Button>
    </Card>
  );
}
