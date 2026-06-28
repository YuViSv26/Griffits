# Запуск Web API (из корня проекта)

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8080
```

Документация Swagger: http://localhost:8080/docs

## Эндпоинты

| Метод | Путь | Описание | Auth |
|-------|------|----------|------|
| GET | `/api/init` | Состояние сессии (замена `/start`) | опционально |
| GET | `/api/me` | Текущий пользователь | да |
| POST | `/api/auth/register` | Регистрация | нет |
| POST | `/api/auth/login` | Вход | нет |
| POST | `/api/auth/forgot-password` | Запрос сброса пароля | нет |
| POST | `/api/auth/reset-password` | Новый пароль по токену | нет |
| GET/PUT | `/api/profile` | Профиль ребёнка | да |
| GET | `/api/assessment/questions` | Вопросы теста Griffiths | да |
| POST | `/api/assessment/submit` | Отправить ответы `[true,false,...]` | да |
| GET | `/api/games/today` | Игра на сегодня | да |
| GET | `/api/progress` | Прогресс по субшкалам | да |
| GET | `/api/chat/history` | История чата | да |
| POST | `/api/chat` | Чат через NordRouter (SSE stream) | да |

## NordRouter

Используется `POST /v1/chat/completions` через OpenAI SDK:
- `NORDROUTER_BASE_URL=https://nordrouter.com/v1`
- `Authorization: Bearer NORDROUTER_API_KEY`

## Авторизация

JWT возвращается в теле ответа и в HttpOnly cookie `griffiths_token`.
Фронтенд может передавать `Authorization: Bearer <token>`.
