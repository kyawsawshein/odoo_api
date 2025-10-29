"""Kafka producer for sending async messages"""

import json
from typing import Dict, Any
from kafka import KafkaProducer
import structlog

from app.config import settings


logger = structlog.get_logger()


class KafkaProducer:
    """Kafka producer for async message processing"""

    _instance = None

    def __init__(self):
        if KafkaProducer._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            self.producer = None
            self._connect()
            KafkaProducer._instance = self

    def _connect(self):
        """Connect to Kafka broker"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda v: v.encode("utf-8") if v else None,
                acks="all",
                retries=3,
                batch_size=16384,
                linger_ms=10,
            )
            logger.info("Kafka producer connected successfully")
        except Exception as e:
            logger.error("Failed to connect to Kafka", error=str(e))
            raise

    @classmethod
    def get_instance(cls):
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = KafkaProducer()
        return cls._instance

    async def send_message(self, topic: str, message: Dict[str, Any], key: str = None):
        """Send message to Kafka topic"""
        try:
            future = self.producer.send(topic=topic, value=message, key=key)

            # Wait for message to be delivered
            result = future.get(timeout=10)

            logger.info(
                "Message sent to Kafka",
                topic=topic,
                partition=result.partition,
                offset=result.offset,
            )

            return True

        except Exception as e:
            logger.error("Failed to send message to Kafka", topic=topic, error=str(e))
            return False

    async def send_bulk_messages(
        self, topic: str, messages: list, key_field: str = None
    ):
        """Send multiple messages to Kafka topic"""
        try:
            for message in messages:
                key = str(message.get(key_field)) if key_field else None
                await self.send_message(topic, message, key)

            logger.info(
                "Bulk messages sent to Kafka", topic=topic, message_count=len(messages)
            )

            return True

        except Exception as e:
            logger.error(
                "Failed to send bulk messages to Kafka", topic=topic, error=str(e)
            )
            return False

    def close(self):
        """Close Kafka producer connection"""
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer closed")


# Global Kafka producer instance
kafka_producer = KafkaProducer.get_instance()
