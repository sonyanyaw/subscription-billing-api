# Subscription Billing API

Асинхронный backend-сервис для управления подписками, счетами и платежами.  
Реализует базовую billing-систему: пользователи могут оформлять подписки, получать счета (invoices), оплачивать их и активировать подписку.

Проект создан с использованием современной архитектуры FastAPI + async SQLAlchemy.

---

# Технологии

- **Python 3.11+**
- **FastAPI**
- **SQLAlchemy (async)**
- **PostgreSQL**
- **Pydantic**
- **Alembic**
- **JWT authentication**
- **Docker / Docker Compose**
- **Pytest**

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

## Stripe Integration

Используется **Payment Intents API**.

**Flow:**
1. Backend создаёт PaymentIntent
2. Возвращает confirmation_url (client_secret)
3. Клиент подтверждает оплату
4. Stripe отправляет webhook
5. Backend:
6. обновляет Payment → succeeded
7. обновляет Invoice → paid
8. активирует Subscription

---

### Webhooks

Endpoint:
```
POST /webhooks/stripe
```

Обрабатывает события:
- payment_intent.succeeded
- payment_intent.payment_failed

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