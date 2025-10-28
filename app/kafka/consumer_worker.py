"""Kafka consumer worker for async message processing"""
import asyncio
import signal
import sys
import structlog

from app.kafka.consumer import create_odoo_consumer


logger = structlog.get_logger()


class ConsumerWorker:
    """Worker for processing Kafka messages"""
    
    def __init__(self):
        self.consumer = None
        self.running = False
    
    async def start(self):
        """Start the consumer worker"""
        try:
            self.consumer = create_odoo_consumer()
            self.running = True
            
            # Register signal handlers
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)
            
            logger.info("Starting Kafka consumer worker")
            
            # Start consuming from all Odoo topics
            topics = [
                "odoo-contacts",
                "odoo-products", 
                "odoo-inventory",
                "odoo-purchase",
                "odoo-sales",
                "odoo-bulk-sync"
            ]
            
            await self.consumer.start_consuming(topics)
            
        except Exception as e:
            logger.error("Failed to start consumer worker", error=str(e))
            raise
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("Received shutdown signal", signal=signum)
        self.running = False
        if self.consumer:
            self.consumer.close()
        sys.exit(0)
    
    async def stop(self):
        """Stop the consumer worker"""
        self.running = False
        if self.consumer:
            self.consumer.close()
        logger.info("Kafka consumer worker stopped")


async def main():
    """Main entry point for consumer worker"""
    worker = ConsumerWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Consumer worker interrupted by user")
    except Exception as e:
        logger.error("Consumer worker failed", error=str(e))
        sys.exit(1)
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())