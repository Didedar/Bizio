# Bizio / Ecomt CRM

**Multi-tenant SaaS CRM for e-commerce sellers with automated financial calculations**

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 📋 Overview

Bizio is a production-ready MVP for a multi-tenant CRM system designed for e-commerce sellers. It provides comprehensive business management features including:

- **Multi-tenant architecture** with user roles and permissions
- **CRM**: Clients, Products, Orders, Deals
- **Supply Chain**: Suppliers, Purchase Orders, Inventory management
- **Financial Module**: Automated calculations for revenue, COGS, gross profit, EBIT, net profit, margins, and break-even analysis
- **Integrations**: Marketplace adapter layer (Wildberries, Kaspi, etc.)
- **Background Jobs**: Celery workers for async tasks
- **Complete API**: RESTful API with OpenAPI/Swagger documentation

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose (recommended)
- OR Python 3.11+, PostgreSQL, Redis (for local development)

### Option 1: Docker Compose (Recommended)

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd Bizio
```

2. **Copy environment file**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start all services**
```bash
docker-compose up --build
```

4. **Access the application**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

5. **Seed demo data** (optional)
```bash
docker-compose exec backend python seed_data.py
```

### Option 2: Local Development

1. **Install dependencies**
```bash
cd backend
pip install -r requirements.txt
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env file with your settings
```

3. **Run migrations** (optional, or use CREATE_TABLES_ON_STARTUP=true)
```bash
alembic upgrade head
```

4. **Seed demo data**
```bash
python seed_data.py
```

5. **Start the server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. **Start Celery worker** (separate terminal)
```bash
celery -A worker.worker worker --loglevel=info
```

## 📚 API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Authentication

The API uses JWT Bearer token authentication.

**Register a new user:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass",
    "full_name": "John Doe",
    "tenant_name": "My Company"
  }'
```

**Login to get access token:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=securepass"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Use the token in subsequent requests:**
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Key Endpoints

#### Core Resources
- `POST /api/v1/tenants/` - Create tenant
- `POST /api/v1/clients/` - Create client
- `POST /api/v1/products/` - Create product
- `POST /api/v1/orders/` - Create order
- `POST /api/v1/deals/` - Create deal

#### Finance
- `GET /api/v1/finance/summary` - Get financial summary

**Example: Finance Summary**
```bash
curl -X GET "http://localhost:8000/api/v1/finance/summary?tenant_id=1&start=2025-01-01&end=2025-01-31&opex=10000&fixed=5000&variable=20000&tax_percent=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
{
  "revenue": "150000.00",
  "cogs": "90000.00",
  "gross_profit": "60000.00",
  "gross_margin_pct": "40.00",
  "opex": "10000.00",
  "ebit": "50000.00",
  "taxes": "5000.00",
  "net_profit": "35000.00",
  "net_margin_pct": "23.33",
  "break_even_revenue": "12500.00"
}
```

## 🗄️ Database

### Migrations (Alembic)

**Create a new migration:**
```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

**Apply migrations:**
```bash
alembic upgrade head
```

**Rollback:**
```bash
alembic downgrade -1
```

### Seed Data

The seed script creates demo data for testing:
- 1 tenant: "Demo Company Ltd"
- 1 user: demo@bizio.com / demo123
- 3 clients
- 5 products
- 6 orders
- 1 supplier

```bash
python backend/seed_data.py
```

## 🧪 Testing

**Run all tests:**
```bash
cd backend
pytest
```

**Run with coverage:**
```bash
pytest --cov=app --cov-report=html
```

**Run specific test file:**
```bash
pytest tests/test_finance.py -v
```

### Test Coverage

Tests include:
- ✅ Unit tests for finance calculations
- ✅ Integration tests for API endpoints
- ✅ Authentication tests
- ✅ CRUD operations tests

## 🏗️ Architecture

```
Bizio/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/         # API endpoints (v1)
│   │   ├── core/        # Config, security
│   │   ├── models.py    # SQLAlchemy models
│   │   ├── schemas.py   # Pydantic schemas
│   │   ├── crud.py      # Database operations
│   │   ├── finance.py   # Financial calculations
│   │   ├── db.py        # Database setup
│   │   └── main.py      # FastAPI app
│   ├── alembic/         # Database migrations
│   ├── tests/           # Unit & integration tests
│   ├── seed_data.py     # Demo data script
│   └── requirements.txt
├── worker/              # Celery background tasks
│   ├── tasks/
│   │   ├── finance_tasks.py
│   │   └── import_tasks.py
│   └── worker.py
├── frontend/            # (Future: React/Vue.js)
├── docker-compose.yml
└── README.md
```

## 📊 Data Models

### Core Entities
- **Tenant**: Multi-tenant organization
- **User**: System users with roles (admin, manager, accountant, etc.)
- **Client**: Customers
- **Product**: Catalog items with SKU, cost, price
- **Order**: Sales orders with items
- **Deal**: Sales pipeline deals

### Supply Chain
- **Supplier**: Product suppliers
- **PurchaseOrder**: Procurement orders
- **Inventory**: Stock levels and reservations

### Financial
- **Invoice**: Billing documents
- **Payment**: Payment records
- **Shipment**: Logistics tracking

### System
- **Integration**: Marketplace connections
- **AuditLog**: Activity tracking
- **Task**: Internal task management
- **FeatureFlag**: Feature toggles

## 🔧 Configuration

### Environment Variables

Key environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:///./dev.db` |
| `SECRET_KEY` | JWT secret key | (generate secure key) |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Security

**Important for Production:**
- Generate a secure `SECRET_KEY` (32+ characters)
- Use PostgreSQL instead of SQLite
- Set `DEBUG=false`
- Configure specific `CORS_ORIGINS`
- Use HTTPS/TLS
- Enable rate limiting
- Set up proper firewall rules

## 🚀 Deployment

### Docker Production

1. Update `.env` with production values
2. Use production-ready docker-compose:

```yaml
# docker-compose.prod.yml
services:
  backend:
    image: your-registry/bizio-backend:latest
    environment:
      - DEBUG=false
      - CREATE_TABLES_ON_STARTUP=false  # Use migrations
    restart: always
```

3. Run migrations before starting:
```bash
docker-compose exec backend alembic upgrade head
```

### Cloud Deployment

Compatible with:
- AWS (ECS, RDS, ElastiCache)
- Google Cloud (Cloud Run, Cloud SQL, Memorystore)
- Azure (Container Instances, Database, Redis Cache)
- Heroku, Render, Railway

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
- Create an issue on GitHub
- Check API documentation at `/docs`
- Review test files for usage examples

## 🎯 Roadmap

- [ ] Frontend admin dashboard (React/Vue)
- [ ] Real marketplace integrations (Wildberries, Kaspi, Ozon)
- [ ] Advanced analytics and forecasting
- [ ] Mobile app
- [ ] Multi-currency support
- [ ] Advanced reporting (PDF/Excel export)
- [ ] Real-time notifications (WebSockets)
- [ ] API rate limiting middleware
- [ ] Comprehensive audit logging

## 📈 Demo Credentials

After running seed script:
- **Email**: demo@bizio.com
- **Password**: demo123
- **Tenant ID**: 1

---

**Built with ❤️ using FastAPI, SQLAlchemy, PostgreSQL, Redis, and Celery**

