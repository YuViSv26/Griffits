# Нейроконсультант Гриффитс

Веб-приложение для родителей младенцев 0–2 лет: развивающие игры и чат-консультант по **Шкале Гриффитс** (субшкалы A–E).

## Возможности

- Регистрация и профиль ребёнка (имя, дата рождения)
- Экспресс-тест Griffiths (5 вопросов Да/Нет)
- **Игра на сегодня** — по возрасту и слабой субшкале
- **Прогресс** — статистика по сферам A–E
- **Чат-консультант** — ответы через [NordRouter](https://nordrouter.com)

## Быстрый старт

### 1. Настройка

```cmd
cd C:\Users\Юлия\Projects\griffiths-baby-bot
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Заполните `.env`: `JWT_SECRET`, `NORDROUTER_API_KEY`.

### 2. Запуск

Дважды кликните (или из cmd):

1. **`start-backend.cmd`** — API на http://localhost:8080  
2. **`start-frontend.cmd`** — сайт на http://localhost:5173  

Проверка API: http://localhost:8080/health

### Ручной запуск

```cmd
:: Окно 1
.\.venv\Scripts\activate
python -m uvicorn backend.main:app --reload --port 8080

:: Окно 2
cd frontend
npm install
npm run dev
```

## Структура

```text
griffiths-baby-bot/
├── backend/           # FastAPI + SQLite + NordRouter
├── frontend/          # React + Tailwind
├── start-backend.cmd
├── start-frontend.cmd
└── requirements.txt
```

## Субшкалы Гриффитс

| Код | Сфера |
|-----|-------|
| A | Двигательная активность |
| B | Личностно-социальная |
| C | Слух и речь |
| D | Зрительно-моторная координация |
| E | Способность к игре |

## API

Документация: http://localhost:8080/docs  
Подробнее: [backend/README.md](backend/README.md)
