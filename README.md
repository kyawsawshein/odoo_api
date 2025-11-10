# Odoo FastAPI Integration

A high-performance FastAPI application designed to integrate with Odoo 19 for real-time data synchronization across multiple business domains including contacts, products, inventory, purchases, sales, deliveries, and accounting.

## Features
<!-- https://zervi-wiki-u34072.vm.elestio.app/s/ZSAA/p/front-end-project-app-test-api-to-odoo-4WcEFZddD7 -->
- **Multi-domain Integration**: Contacts, Products, Inventory, Purchases, Sales, Deliveries, Accounting
- **High Concurrency**: Supports 1000+ concurrent users
- **Async Processing**: Kafka integration for background processing
- **Caching**: Redis for performance optimization
- **Flexible API**: REST API and GraphQL endpoints
- **Authentication**: JWT-based authentication with Odoo session management
- **Real-time Sync**: Bidirectional synchronization with Odoo

## Architecture

```
External UI → FastAPI Gateway → Business Logic → Odoo Integration
                    ↓
              Kafka (Async Processing)
                    ↓
              Redis (Caching)
                    ↓
            PostgreSQL (Local Storage)
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Running with Docker

1. Clone the repository:
```bash
git clone <repository-url>
cd odoo_api
```

2. Create environment file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start services:
```bash
docker-compose up -d
```

4. Access the application:
   - API Documentation: http://localhost:8000/docs
   - GraphQL Playground: http://localhost:8000/graphql
   - Health Check: http://localhost:8000/health

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/odoo_api"
export REDIS_URL="redis://localhost:6379/0"
export ODOO_URL="http://localhost:8069"
export SECRET_KEY="your-secret-key"
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/token` - Login and get JWT token
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/odoo-login` - Authenticate with Odoo
- `GET /api/v1/auth/me` - Get current user info

### Contacts
- `GET /api/v1/contacts` - List contacts
- `POST /api/v1/contacts` - Create contact
- `GET /api/v1/contacts/{id}` - Get contact
- `PUT /api/v1/contacts/{id}` - Update contact

### Products
- `GET /api/v1/products` - List products
- `POST /api/v1/products` - Create product
- `GET /api/v1/products/{id}` - Get product
- `PUT /api/v1/products/{id}` - Update product

### Inventory
- `GET /api/v1/inventory` - Get inventory data
- `POST /api/v1/inventory/sync` - Sync inventory with Odoo

### Bulk Operations
- `POST /api/v1/bulk-sync` - Bulk sync multiple entities

## GraphQL API

The GraphQL API provides flexible querying capabilities:

```graphql
# Query contacts
query {
  contacts(limit: 10, search: "john") {
    id
    name
    email
    phone
  }
}

# Create product
mutation {
  createProduct(product: {
    name: "New Product"
    listPrice: 99.99
    type: "product"
  }) {
    success
    message
    odooId
    localId
  }
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | - |
| `REDIS_URL` | Redis connection URL | - |
| `ODOO_URL` | Odoo instance URL | http://localhost:8069 |
| `ODOO_DATABASE` | Odoo database name | odoo |
| `ODOO_USERNAME` | Odoo username | admin |
| `ODOO_PASSWORD` | Odoo password | admin |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka brokers | localhost:9092 |
| `SECRET_KEY` | JWT secret key | - |
| `DEBUG` | Debug mode | False |

### Odoo Integration

The application supports both XML-RPC and JSON-RPC for Odoo integration. Configure your Odoo instance:

1. Enable XML-RPC in Odoo configuration
2. Create API user with appropriate permissions
3. Configure the connection in environment variables

## Performance Optimization

### Caching Strategy
- **L1 Cache**: In-memory caching for frequently accessed data
- **L2 Cache**: Redis for distributed caching
- **Cache Invalidation**: Automatic invalidation on data changes

### Concurrency Handling
- **Async/Await**: All operations are non-blocking
- **Connection Pooling**: Database and Odoo connection pooling
- **Background Tasks**: Kafka for async processing
- **Rate Limiting**: Per-user rate limiting

### Kafka Topics
- `odoo-contacts` - Contact synchronization
- `odoo-products` - Product synchronization
- `odoo-inventory` - Inventory synchronization
- `odoo-purchase` - Purchase order processing
- `odoo-sales` - Sales order processing
- `odoo-bulk-sync` - Bulk synchronization

## Development

### Project Structure
```
odoo_api/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── database.py          # Database setup
│   ├── auth/                # Authentication
│   ├── api/                 # REST API
│   ├── graphql/             # GraphQL API
│   ├── services/            # Business logic
│   ├── odoo/                # Odoo integration
│   ├── kafka/               # Kafka integration
│   └── cache/               # Redis caching
├── tests/                   # Test suite
├── docker-compose.yml       # Docker setup
└── requirements.txt         # Dependencies
```

### Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

### Code Quality
```bash
# Format code
black app/ tests/

# Check types
mypy app/

# Lint code
flake8 app/ tests/
```

## Deployment

### Production Deployment

1. Set `DEBUG=False` in environment
2. Configure proper database and Redis connections
3. Set up SSL/TLS certificates
4. Configure monitoring and logging
5. Set up backup strategies

### Scaling

- **Horizontal Scaling**: Deploy multiple API instances
- **Load Balancing**: Use nginx or similar load balancer
- **Database**: PostgreSQL with read replicas
- **Cache**: Redis cluster for distributed caching
- **Message Queue**: Kafka cluster for high throughput

## Monitoring

- **Health Checks**: `/health` endpoint
- **Metrics**: Prometheus metrics endpoint
- **Logging**: Structured logging with structlog
- **Tracing**: Distributed tracing support

## Security

- **Authentication**: JWT tokens with refresh
- **Authorization**: Role-based access control
- **Input Validation**: Pydantic models for all inputs
- **Rate Limiting**: Per-user rate limiting
- **CORS**: Configurable CORS settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.