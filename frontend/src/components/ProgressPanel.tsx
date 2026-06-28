import { useEffect, useState } from "react";
import { api, type ProgressResponse } from "../api/client";
import { Button, Card, Spinner } from "./ui";

export function ProgressPanel() {
  const [data, setData] = useState<ProgressResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = () => {
    setLoading(true);
    api
      .getProgress()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  if (loading) {
    return (
      <Card className="flex items-center justify-center p-12">
        <Spinner />
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6 text-center text-red-600">
        {error}
        <Button className="mt-4" onClick={load}>
          Обновить
        </Button>
      </Card>
    );
  }

  if (!data) return null;

  if (data.message || data.items.length === 0) {
    return (
      <Card className="p-6 text-center">
        <p className="text-slate-600">{data.message}</p>
        <p className="mt-2 text-sm text-slate-500">
          Пройдите тест в боковом меню
        </p>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold">Прогресс {data.baby_name}</h2>
        {data.last_test_date && (
          <p className="text-sm text-slate-500">
            Последний тест: {data.last_test_date}
          </p>
        )}
      </div>
      <div className="space-y-4">
        {data.items.map((item) => (
          <div key={item.subscale}>
            <div className="mb-1 flex justify-between text-sm">
              <span className="font-medium">{item.name}</span>
              <span className="text-slate-500">
                {item.score}%
                {item.delta != null && item.delta !== 0 && (
                  <span
                    className={
                      item.delta > 0 ? "text-green-600" : "text-red-600"
                    }
                  >
                    {" "}
                    ({item.delta > 0 ? "+" : ""}
                    {item.delta}%)
                  </span>
                )}
              </span>
            </div>
            {item.skill && (
              <p className="mb-1 text-xs text-slate-600">{item.skill}</p>
            )}
            <div className="font-mono text-xs text-brand-600">{item.bar}</div>
          </div>
        ))}
      </div>
      <div className="mt-6 grid gap-3 rounded-xl bg-slate-50 p-4 text-sm sm:grid-cols-2">
        <p>
          <span className="font-medium">Сильная сторона:</span> {data.strongest}
        </p>
        <p>
          <span className="font-medium">Развивать:</span> {data.weakest}
        </p>
      </div>
      <Button variant="secondary" className="mt-4" onClick={load}>
        Обновить
      </Button>
    </Card>
  );
}
