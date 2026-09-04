# TASK 4 - Role-Based Microservice API Ecosystem

## Architecture
- **auth-service (8001)**: JWT issuance, verification, RBAC tiers [ADMIN, MANAGER, USER]
- **product-service (8002)**: Protected CRUD, role checks via JWT
- **order-service (8003)**: Receives intense transactions, pushes to RabbitMQ queue, background consumer processes without DB locks
- **rabbitmq**: Message broker (management UI at 15672)

## Networks Isolation (Docker Compose)
- backend-net: common
- auth-net: only auth-service
- product-net: only product-service
- order-net: only order-service
- broker-net: rabbitmq <-> order-service & auth-service

## How to Run
docker-compose up --build

## Test Users
- admin@example.com / admin123 -> ADMIN
- manager@example.com / manager123 -> MANAGER
- user@example.com / user123 -> USER

## Testing
python test_verification.py

## What this satisfies
- JWT + RBAC layers
- Async broker (RabbitMQ) avoids DB locks
- Container orchestration with separate networks
- Automated endpoint verification
"# rbac-microservices-api" 
