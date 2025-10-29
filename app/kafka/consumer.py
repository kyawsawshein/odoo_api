"""Kafka consumer for processing async messages"""

import json
import asyncio
from typing import Dict, Any, Callable
from kafka import KafkaConsumer
import structlog

from app.config import settings


logger = structlog.get_logger()


class KafkaConsumer:
    """Kafka consumer for processing async messages"""

    def __init__(self, group_id: str = None):
        self.consumer = None
        self.group_id = group_id or settings.KAFKA_GROUP_ID
        self.handlers = {}
        self._connect()

    def _connect(self):
        """Connect to Kafka broker"""
        try:
            self.consumer = KafkaConsumer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=self.group_id,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                key_deserializer=lambda v: v.decode("utf-8") if v else None,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
            )
            logger.info("Kafka consumer connected successfully", group_id=self.group_id)
        except Exception as e:
            logger.error("Failed to connect to Kafka", error=str(e))
            raise

    def register_handler(self, topic: str, handler: Callable):
        """Register message handler for topic"""
        self.handlers[topic] = handler
        logger.info("Handler registered for topic", topic=topic)

    async def process_message(self, topic: str, message: Dict[str, Any]):
        """Process single message"""
        try:
            handler = self.handlers.get(topic)
            if handler:
                await handler(message)
                logger.info("Message processed successfully", topic=topic)
            else:
                logger.warning("No handler registered for topic", topic=topic)
        except Exception as e:
            logger.error("Failed to process message", topic=topic, error=str(e))

    async def start_consuming(self, topics: list):
        """Start consuming messages from specified topics"""
        try:
            self.consumer.subscribe(topics)
            logger.info("Started consuming from topics", topics=topics)

            for message in self.consumer:
                await self.process_message(
                    message.topic,
                    {
                        "key": message.key,
                        "value": message.value,
                        "partition": message.partition,
                        "offset": message.offset,
                    },
                )

        except Exception as e:
            logger.error("Error in consumer loop", error=str(e))
        finally:
            self.close()

    async def start_consuming_single_topic(self, topic: str):
        """Start consuming messages from single topic"""
        await self.start_consuming([topic])

    def close(self):
        """Close Kafka consumer connection"""
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer closed")


class OdooMessageHandler:
    """Handler for Odoo-related Kafka messages"""

    def __init__(self):
        self.logger = logger.bind(handler="OdooMessageHandler")

    async def handle_contact_message(self, message: Dict[str, Any]):
        """Handle contact-related messages"""
        try:
            action = message["value"].get("action")
            user_id = message["value"].get("user_id")
            contact_data = message["value"].get("contact_data")

            self.logger.info(
                "Processing contact message", action=action, user_id=user_id
            )

            # Here you would implement the actual Odoo synchronization logic
            # This could involve database operations, API calls, etc.

            if action == "create":
                # Create contact in Odoo
                pass
            elif action == "update":
                # Update contact in Odoo
                pass

        except Exception as e:
            self.logger.error(
                "Failed to process contact message", error=str(e), message=message
            )

    async def handle_product_message(self, message: Dict[str, Any]):
        """Handle product-related messages"""
        try:
            action = message["value"].get("action")
            user_id = message["value"].get("user_id")
            product_data = message["value"].get("product_data")

            self.logger.info(
                "Processing product message", action=action, user_id=user_id
            )

            # Implement product synchronization logic

        except Exception as e:
            self.logger.error(
                "Failed to process product message", error=str(e), message=message
            )

    async def handle_inventory_message(self, message: Dict[str, Any]):
        """Handle inventory-related messages"""
        try:
            action = message["value"].get("action")
            user_id = message["value"].get("user_id")

            self.logger.info(
                "Processing inventory message", action=action, user_id=user_id
            )

            # Implement inventory synchronization logic

        except Exception as e:
            self.logger.error(
                "Failed to process inventory message", error=str(e), message=message
            )

    async def handle_bulk_sync_message(self, message: Dict[str, Any]):
        """Handle bulk synchronization messages"""
        try:
            user_id = message["value"].get("user_id")
            data = message["value"].get("data")

            self.logger.info(
                "Processing bulk sync message",
                user_id=user_id,
                data_types=list(data.keys()) if data else [],
            )

            # Implement bulk synchronization logic
            # This would process multiple entities in batch

        except Exception as e:
            self.logger.error(
                "Failed to process bulk sync message", error=str(e), message=message
            )


# Create and configure consumer
def create_odoo_consumer():
    """Create and configure Odoo message consumer"""
    consumer = KafkaConsumer(group_id="odoo-processors")
    handler = OdooMessageHandler()

    # Register handlers for different topics
    consumer.register_handler("odoo-contacts", handler.handle_contact_message)
    consumer.register_handler("odoo-products", handler.handle_product_message)
    consumer.register_handler("odoo-inventory", handler.handle_inventory_message)
    consumer.register_handler(
        "odoo-purchase", handler.handle_contact_message
    )  # Reuse for now
    consumer.register_handler(
        "odoo-sales", handler.handle_contact_message
    )  # Reuse for now
    consumer.register_handler("odoo-bulk-sync", handler.handle_bulk_sync_message)

    return consumer
