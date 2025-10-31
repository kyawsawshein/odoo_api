# Kafka Docker Troubleshooting Guide

## Issue Fixed: Port Conflict Error

**Error Message:**
```
ERROR Exiting Kafka due to fatal exception (kafka.Kafka$)
java.lang.IllegalArgumentException: requirement failed: Each listener must have a different port, listeners: PLAINTEXT://0.0.0.0:9092,PLAINTEXT_HOST://0.0.0.0:9092
```

## Root Cause

The Kafka configuration was trying to use the same port (9092) for two different listeners:
- `PLAINTEXT://0.0.0.0:9092` (internal container communication)
- `PLAINTEXT_HOST://0.0.0.0:9092` (host machine communication)

## Solution Applied

### Before (Problematic Configuration):
```yaml
environment:
  KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,PLAINTEXT_HOST://localhost:9092
```

### After (Fixed Configuration):
```yaml
environment:
  KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
  KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT
```

## Updated Docker Compose Configuration

```yaml
kafka:
  image: confluentinc/cp-kafka:7.4.0
  depends_on:
    - zookeeper
  ports:
    - "9092:9092"
  environment:
    KAFKA_BROKER_ID: 1
    KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
    KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT
    KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
    KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
```

## How to Restart Kafka

### 1. Stop and Remove Existing Containers
```bash
cd odoo_api
docker-compose down
```

### 2. Remove Kafka Data (if needed)
```bash
docker volume prune
```

### 3. Start Services
```bash
docker-compose up -d kafka
```

### 4. Verify Kafka is Running
```bash
docker-compose logs kafka
```

You should see:
```
[2025-10-30 03:28:00,000] INFO [KafkaServer id=1] started (kafka.server.KafkaServer)
```

### 5. Test Kafka Connection
```bash
docker-compose exec kafka kafka-topics --bootstrap-server kafka:9092 --list
```

## Alternative Configuration (If Still Having Issues)

If you need both internal and external access, use this configuration:

```yaml
kafka:
  image: confluentinc/cp-kafka:7.4.0
  depends_on:
    - zookeeper
  ports:
    - "9092:9092"
    - "9093:9093"
  environment:
    KAFKA_BROKER_ID: 1
    KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,PLAINTEXT_HOST://localhost:9093
    KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
    KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
    KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
```

Then update your application to use:
- `kafka:9092` for internal container communication
- `localhost:9093` for external host communication

## Common Kafka Issues and Solutions

### 1. Zookeeper Connection Issues
```bash
# Check if Zookeeper is running
docker-compose logs zookeeper

# Restart Zookeeper if needed
docker-compose restart zookeeper
```

### 2. Kafka Not Starting
```bash
# Check Kafka logs
docker-compose logs kafka

# Check if port 9092 is available
netstat -tulpn | grep 9092
```

### 3. Topic Creation Issues
```bash
# Create a test topic manually
docker-compose exec kafka kafka-topics --create \
  --bootstrap-server kafka:9092 \
  --replication-factor 1 \
  --partitions 1 \
  --topic test-topic
```

### 4. Consumer/Producer Connection Issues
```bash
# Test producer
docker-compose exec kafka kafka-console-producer \
  --broker-list kafka:9092 \
  --topic test-topic

# Test consumer (in another terminal)
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server kafka:9092 \
  --topic test-topic \
  --from-beginning
```

## Environment Variables

Make sure your `.env` file has:
```env
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_GROUP_ID=odoo-api-group
```

## Network Configuration

The services are configured to use the external network `odoo19_odoo19-net`. Make sure this network exists:

```bash
docker network ls | grep odoo19_odoo19-net
```

If it doesn't exist, create it:
```bash
docker network create odoo19_odoo19-net
```

## Health Checks

All services include health checks:
- **Zookeeper**: Port 2181 connectivity
- **Kafka**: Topic listing capability
- **Redis**: Ping command

Check service health:
```bash
docker-compose ps
```

The Kafka Docker configuration is now fixed and should start without port conflict errors.