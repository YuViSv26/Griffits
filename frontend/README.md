# Frontend — Нейроконсультант Гриффитс

React + Tailwind SPA с чат-интерфейсом, подключённым к FastAPI backend.

## Запуск

```bash
# Терминал 1 — backend
cd ..
uvicorn backend.main:app --reload --port 8080

# Терминал 2 — frontend
npm install
npm run dev
```

Откройте http://localhost:5173

Vite проксирует `/api` → `http://localhost:8080`.

## Сборка

```bash
npm run build
npm run preview
```

## Экраны

1. **Вход / Регистрация** — JWT + cookie
2. **Онбординг** — имя, дата рождения, опциональный тест Griffiths
3. **Dashboard** — чат (NordRouter SSE), игра, тест, прогресс, профиль

## Стек

- React 19 + TypeScript
- Tailwind CSS 4
- Vite 6
