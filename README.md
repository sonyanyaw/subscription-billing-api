# Subscription Billing API

Асинхронный backend-сервис для управления подписками, счетами и платежами.  
Реализует billing-систему: пользователи оформляют подписки, получают счета (invoices), оплачивают их через Stripe или YooKassa и активируют подписку.

Включает admin-дашборд (статика, без фреймворков) и Telegram-бот для демонстрации полного флоу.
Проект создан с использованием современной архитектуры FastAPI + async SQLAlchemy.

---

# Технологии

- **Python 3.11+**
- **FastAPI** + **SQLAlchemy (async)** + **asyncpg**
- **PostgreSQL 17** (миграции через **Alembic**)
- **Redis** (сервис в Docker Compose)
- **Pydantic v2** + pydantic-settings
- **JWT** (access + refresh) + bcrypt
- **Stripe** (USD) и **YooKassa** (RUB) + Mock-провайдер
- **APScheduler** — периодические задачи (истечение подписок)
- **python-telegram-bot** — демо-бот
- **Docker / Docker Compose**
- **Pytest** + pytest-asyncio

---

# Запуск

Через Docker Compose (сервисы: `db`, `redis`, `app`, `seed`, `test`, `bot`).

```bash
# 1. Скопировать переменные окружения и заполнить ключи
cp .env.example .env

# 2. Поднять БД и Redis
docker compose up -d db redis

# 3. Применить миграции
docker compose run --rm app alembic upgrade head

# 4. Заполнить планы (Free / Pro / Enterprise с ценами в USD и RUB)
docker compose run --rm seed

# 5. Запустить API
docker compose up app
```

После старта:

| Что | Где |
|---|---|
| Swagger / OpenAPI | http://localhost:8000/docs |
| Admin dashboard | http://localhost:8000/static/dashboard.html |
| Health-check | http://localhost:8000/health |

Тесты:
```bash
docker compose run --rm test
```

Ключевые переменные окружения (см. `.env.example`): `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`,
`STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET`, `YOOKASSA_SHOP_ID` / `YOOKASSA_SECRET_KEY`,
`TELEGRAM_TOKEN` / `TELEGRAM_ADMIN_CHAT_ID`.

---

# Функциональность

### Аутентификация

- регистрация пользователя
- login
- JWT авторизация
- получение текущего пользователя

---

### Подписки

Пользователь может:

- создать подписку
- просмотреть свою подписку
- управлять статусом подписки

Статусы подписки:

- `incomplete`
- `active`
- `canceled`
- `expired`

---

### Billing

Billing состоит из трёх сущностей:

Subscription -> Invoice -> Payment

---

#### Invoices

Счёт на оплату подписки.

Пользователь может:

- получить список своих счетов
- проверить статус счета

Статусы:

- draft
- open
- paid
- failed

---

#### Payments

Платёж — это попытка оплаты счета.

Функции:

- создание платежа
- подтверждение платежа
- обновление статуса счета
- активация подписки после успешной оплаты

Статусы:

- pending
- succeeded
- failed

---

## Платёжные провайдеры

Абстракция `PaymentProviderBase` + фабрика `get_provider()`. Реализованы:

- **Stripe** (USD/EUR/GBP) — Payment Intents API
- **YooKassa** (RUB) — Payments API
- **Mock** — для тестов без внешних зависимостей

При создании платежа валюта счёта проверяется на совместимость с провайдером
(Stripe не примет RUB, YooKassa — только RUB).

**Общий flow:**
1. Backend создаёт платёж у провайдера → возвращает `confirmation_url`
2. Клиент оплачивает на стороне провайдера
3. Провайдер отправляет webhook
4. Backend: Payment → `succeeded`, Invoice → `paid`, Subscription → `active`

### Мультивалютные цены

Цена вынесена из `Plan` в таблицу `plan_prices` (план → несколько цен в разных валютах).
Валюта фиксируется на уровне подписки (`Subscription.currency`); счёт и продления берут
цену по паре `(plan_id, currency)`.

---

### Webhooks

```
POST /webhooks/stripe     # payment_intent.succeeded / payment_intent.payment_failed (проверка подписи)
POST /webhooks/yookassa   # payment.succeeded / payment.canceled
```

Каждое входящее событие персистится в таблицу `webhook_events`
(`received` → `processed`/`failed`); при ошибке обработки отправляется Telegram-алерт.

---

## Admin Dashboard

Статический дашборд (`static/dashboard.html` + `.css` + `.js`, без фреймворков):
таблицы подписчиков/подписок/счетов/платежей с сортировкой, фильтрами, поиском и
пагинацией; drill-down по подписке; CRUD планов; ручное подтверждение платежей;
лог webhook-событий; экспорт в CSV.

## Telegram-бот

Демо-флоу: `/start`, `/register`, `/login`, `/plans`, `/subscribe`, `/me`,
`/invoices`, `/pay`, `/cancel` с inline-клавиатурами.

## Прочее

- **Usage-лимит** по `api_limit` плана (429 при превышении) — FastAPI-dependency `check_usage_limit`.
- **APScheduler** — `expire_subscriptions` каждые 6 часов (`active → past_due → canceled`).

---

## Admin API

Все admin endpoints требуют роль admin.

---

### Subscriptions
Получить все подписки:
```
GET /admin/subscriptions
```

Получить активных подписчиков (с user + plan):
```
GET /admin/subscriptions/subscribers
```

---

### Payments
Получить все платежи:
```
GET /admin/payments
```

---

### Invoices
Получить список счетов с пагинацией:
```
GET /admin/invoices?limit=50&offset=0
```

---

### Plans
CRUD планов и цен:
```
GET    /admin/plans          # список (включая неактивные), с ценами
POST   /admin/plans          # создать план с ценами в нескольких валютах
PUT    /admin/plans/{id}     # обновить план и заменить цены
DELETE /admin/plans/{id}     # удалить (или деактивировать, если есть подписки)
```

### Webhooks
```
GET /admin/webhooks?limit=50&offset=0   # лог webhook-событий из БД
```

---