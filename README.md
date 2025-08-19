# Eagle Bank API - FastAPI Implementation

A comprehensive banking API built with FastAPI, featuring advanced Python patterns, Keycloak authentication, and cloud-native deployment capabilities.

## 🏗️ Architecture Overview

This project demonstrates enterprise-grade API development with:

- **Custom FastAPI Application**: Extended FastAPI with enhanced middleware and event publishing
- **Keycloak Authentication**: JWT-based authentication with role-based access control
- **Design Patterns**: Factory, Adapter, Facade, Repository, and Dependency Injection patterns
- **Event-Driven Architecture**: Redis-based event system with async publishing/subscription
- **Domain-Driven Design**: Clean architecture with separated concerns
- **Cloud-Native Deployment**: Docker and Kubernetes ready

## 🚀 Features

### Core API Functionality
- **User Management**: CRUD operations with Keycloak integration
- **Account Operations**: Account creation, management, and balance tracking
- **Transaction Processing**: Async transaction handling with concurrent processing
- **Audit Logging**: Comprehensive audit trail for all operations

### Advanced Python Patterns
- **Meta-programming**: Dynamic class creation and method decoration
- **Inheritance**: Custom FastAPI classes and domain entity hierarchies
- **Decorators**: Authentication, rate limiting, and audit decorators
- **Context Variables**: Request context management with contextvars
- **Async/Await**: Full async implementation with concurrent operations

### Security Features
- **JWT Authentication**: Keycloak-based token validation
- **Rate Limiting**: Request throttling with Redis backend
- **Input Validation**: Pydantic schemas with comprehensive validation
- **SQL Injection Protection**: Parameterized queries with SQLAlchemy
- **CORS Configuration**: Secure cross-origin resource sharing

## Features

- **Advanced Python Patterns**: Meta-programming, inheritance, decorators, context variables
- **Design Patterns**: Factory, Adapter, Facade, Iterator, Observer
- **Security**: Keycloak integration, JWT tokens, role-based access control
- **Architecture**: Event-driven, async/await, dependency injection
- **Containerization**: Docker & Kubernetes ready
- **Monitoring**: Prometheus metrics, structured logging
- **Testing**: Comprehensive test suite with async support

## Quick Start

### Using Docker Compose

```bash
# Copy environment variables
cp .env.example .env

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f app
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env

# Start PostgreSQL and Redis (using Docker)
docker-compose up -d db redis keycloak

# Run database migrations
alembic upgrade head

# Start the application
uvicorn app.main:app --reload
```

## API Documentation

- **OpenAPI/Swagger**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Architecture

### Project Structure

```
app/
├── main.py                 # Application entry point
├── core/                   # Core application components
│   ├── __init__.py
│   ├── app.py             # Custom FastAPI application
│   ├── config.py          # Configuration management
│   ├── security.py        # Security utilities
│   ├── events.py          # Event system
│   └── celery.py          # Celery configuration
├── api/                   # API layer
│   ├── __init__.py
│   ├── dependencies.py    # FastAPI dependencies
│   ├── middleware.py      # Custom middleware
│   └── v1/               # API version 1
│       ├── __init__.py
│       ├── accounts.py
│       ├── transactions.py
│       └── users.py
├── domain/               # Domain layer (business logic)
│   ├── __init__.py
│   ├── entities/         # Domain entities
│   ├── services/         # Domain services
│   └── events/           # Domain events
├── infrastructure/       # Infrastructure layer
│   ├── __init__.py
│   ├── database/         # Database related
│   ├── external/         # External service adapters
│   └── repositories/     # Data access patterns
├── auth/                 # Authentication & Authorization
│   ├── __init__.py
│   ├── keycloak.py       # Keycloak integration
│   ├── decorators.py     # Auth decorators
│   └── context.py        # Auth context variables
└── tests/                # Test suite
    ├── __init__.py
    ├── conftest.py
    ├── unit/
    ├── integration/
    └── e2e/
```

### Design Patterns Used

1. **Factory Pattern**: Creating different types of accounts and transactions
2. **Adapter Pattern**: External service integrations (Keycloak, external APIs)
3. **Facade Pattern**: Simplified interfaces for complex operations
4. **Observer Pattern**: Event-driven architecture for notifications
5. **Strategy Pattern**: Different authentication strategies
6. **Dependency Injection**: FastAPI's dependency system

## Security Features

- **Keycloak Integration**: Enterprise-grade identity management
- **JWT Token Validation**: Secure API access
- **Role-Based Access Control**: Fine-grained permissions
- **Rate Limiting**: Protection against abuse
- **Input Validation**: Pydantic models with strict validation
- **CORS Configuration**: Controlled cross-origin requests

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test category
pytest tests/unit/
pytest tests/integration/
```

### Code Quality

```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Deployment

### Kubernetes

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -l app=eagle-bank-api

# View logs
kubectl logs -f deployment/eagle-bank-api
```

### Environment Variables

See `.env.example` for all available configuration options.

## Monitoring

- **Health Checks**: `/health` endpoint
- **Metrics**: Prometheus metrics on `/metrics`
- **Logging**: Structured JSON logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License