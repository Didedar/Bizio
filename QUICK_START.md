# 🚀 Быстрый старт - Bizio CRM

## За 2 минуты до запуска!

### Вариант 1: Автоматический запуск (Рекомендуется)

```bash
cd /Users/sabyrhandarhan/Desktop/Bizio
./start.sh
```

Скрипт автоматически:
- Запустит Docker Compose
- Создаст базу данных
- Предложит загрузить демо-данные
- Выведет ссылки для доступа

### Вариант 2: Ручной запуск

```bash
# 1. Перейти в директорию проекта
cd /Users/sabyrhandarhan/Desktop/Bizio

# 2. Запустить все сервисы
docker-compose up --build

# 3. В НОВОМ терминале: загрузить demo data
docker-compose exec backend python seed_data.py
```

## 📍 Куда идти после запуска

1. **Swagger UI (интерактивная документация):**
   ```
   http://localhost:8000/docs
   ```

2. **Проверить здоровье API:**
   ```bash
   curl http://localhost:8000/
   ```

3. **Залогиниться (получить токен):**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=demo@bizio.com&password=demo123"
   ```

4. **Протестировать finance endpoint:**
   ```bash
   curl "http://localhost:8000/api/v1/finance/summary?tenant_id=1&opex=100000&fixed=50000&tax_percent=10"
   ```

## 🔑 Demo credentials

- **Email:** `demo@bizio.com`
- **Password:** `demo123`
- **Tenant ID:** `1`

## 🧪 Запуск тестов

```bash
# Все тесты
docker-compose exec backend pytest -v

# С coverage
docker-compose exec backend pytest --cov=app --cov-report=term

# Только finance тесты
docker-compose exec backend pytest tests/test_finance.py -v
```

## 📚 Полезные команды

```bash
# Посмотреть логи
docker-compose logs -f

# Посмотреть логи только backend
docker-compose logs -f backend

# Остановить все сервисы
docker-compose down

# Перезапустить сервис
docker-compose restart backend

# Выполнить команду внутри контейнера
docker-compose exec backend python seed_data.py

# Создать миграцию Alembic
docker-compose exec backend alembic revision --autogenerate -m "Description"

# Применить миграции
docker-compose exec backend alembic upgrade head
```

## 🛠️ Структура проекта (основное)

```
Bizio/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   │   ├── auth.py      # 🔐 Аутентификация
│   │   │   ├── finance.py   # 💰 Финансы (CORE)
│   │   │   ├── orders.py    # 📦 Заказы
│   │   │   └── ...
│   │   ├── core/
│   │   │   ├── config.py    # ⚙️ Конфигурация
│   │   │   └── security.py  # 🔒 JWT, bcrypt
│   │   ├── models.py        # 🗄️ SQLAlchemy models (30+ таблиц)
│   │   ├── schemas.py       # 📋 Pydantic schemas
│   │   ├── crud.py          # 🔧 Database operations
│   │   ├── finance.py       # 💵 Financial calculations
│   │   └── main.py          # 🚀 FastAPI app
│   ├── tests/               # 🧪 Unit & integration tests
│   ├── alembic/             # 📊 Database migrations
│   └── seed_data.py         # 🌱 Demo data
├── worker/                  # ⚙️ Celery background tasks
├── docker-compose.yml       # 🐳 Docker setup
├── README.md                # 📖 Полная документация
├── API_EXAMPLES.md          # 📝 Примеры API
└── CHECKLIST.md             # ✅ Что сделано

```

## 🔧 Локальная разработка (без Docker)

```bash
# 1. Установить зависимости
cd backend
pip install -r requirements.txt

# 2. Создать .env
cp .env.example .env
# Отредактировать DATABASE_URL и другие настройки

# 3. Запустить backend
uvicorn app.main:app --reload --port 8000

# 4. В новом терминале: worker
celery -A worker.worker worker --loglevel=info

# 5. Загрузить demo data
python seed_data.py
```

## 📞 Основные API endpoints

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/v1/auth/register` | POST | Регистрация |
| `/api/v1/auth/token` | POST | Логин (получить JWT) |
| `/api/v1/auth/me` | GET | Текущий пользователь |
| `/api/v1/tenants/` | POST/GET | Управление тенантами |
| `/api/v1/clients/` | POST/GET | Клиенты |
| `/api/v1/products/` | POST/GET | Товары |
| `/api/v1/orders/` | POST/GET | Заказы |
| `/api/v1/deals/` | POST/GET | Сделки |
| `/api/v1/finance/summary` | GET | 💰 **Финансовая сводка** |
| `/api/v1/suppliers/` | POST/GET | Поставщики |
| `/api/v1/inventory/` | GET/POST | Инвентарь |

## 🎯 Пример работы с API

### 1. Регистрация и логин

```bash
# Регистрация
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "mypassword",
    "full_name": "John Doe",
    "tenant_name": "My Company"
  }'

# Логин
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=mypassword" \
  | jq -r '.access_token')

echo "Token: $TOKEN"
```

### 2. Создать товар

```bash
curl -X POST "http://localhost:8000/api/v1/products/?tenant_id=1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "iPhone 15",
    "sku": "IPH-15",
    "default_cost": "500000",
    "default_price": "750000",
    "category": "Electronics"
  }'
```

### 3. Создать заказ

```bash
curl -X POST "http://localhost:8000/api/v1/orders/?tenant_id=1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1,
    "channel": "web",
    "items": [{
      "product_id": 1,
      "title": "iPhone 15",
      "qty": 2,
      "unit_price": "750000",
      "unit_cost": "500000"
    }]
  }'
```

### 4. Получить финансовую сводку

```bash
curl "http://localhost:8000/api/v1/finance/summary?tenant_id=1&opex=500000&fixed=200000&tax_percent=10" \
  -H "Authorization: Bearer $TOKEN"
```

Результат:
```json
{
  "revenue": "1500000.00",
  "cogs": "1000000.00",
  "gross_profit": "500000.00",
  "gross_margin_pct": "33.33",
  "ebit": "0.00",
  "net_profit": "-700000.00",
  "break_even_revenue": "400000.00"
}
```

## ❓ FAQ

### Q: Как изменить порт API?

A: Отредактируйте `docker-compose.yml`:
```yaml
backend:
  ports:
    - "8080:8000"  # вместо 8000:8000
```

### Q: Как подключиться к базе данных?

A: Postgres доступен на `localhost:5432`:
```bash
psql -h localhost -U bizio -d bizio_db
# Password: bizio_pass
```

### Q: Ошибка "port is already allocated"?

A: Порт занят. Остановите другие сервисы или измените порт в docker-compose.yml

### Q: Как сбросить базу данных?

A:
```bash
docker-compose down -v  # удалит volumes
docker-compose up --build
docker-compose exec backend python seed_data.py
```

## 📖 Дополнительная документация

- **README.md** - Полная документация проекта
- **API_EXAMPLES.md** - Подробные примеры API
- **DEPLOY.md** - Production deployment
- **CHECKLIST.md** - Что реализовано

## 🆘 Помощь

Если что-то не работает:

1. Проверьте логи: `docker-compose logs -f`
2. Убедитесь, что Docker запущен
3. Проверьте, что порты 8000, 5432, 6379 свободны
4. Попробуйте пересобрать: `docker-compose up --build --force-recreate`

---

**Готово! Теперь вы можете начать работу с Bizio CRM! 🎉**

