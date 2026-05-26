from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = (
    "postgresql+asyncpg://"
    "opi:admin123"
    "@127.0.0.1:5435/keng-zervi-erp.cloudpepper.site"
)


engine = create_async_engine(
    DATABASE_URL,
    echo=True,
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


  # ssh-tunnel:
  #   image: alpine
  #   container_name: ssh-tunnel
  #   command: >
  #     sh -c "
  #     apk add --no-cache openssh &&
  #     ssh
  #     -i /root/.ssh/id_ed25519
  #     -o StrictHostKeyChecking=no
  #     -N
  #     -L 0.0.0.0:5432:localhost:5432
  #     root@keng-zervi-erp.cloudpepper.site
  #     "
  #   volumes:
  #     - ~/.ssh/id_ed25519:/root/.ssh/id_ed25519:ro
  #   ports:
  #     - "5435:5432"
  #   networks:
  #     - odoo19_odoo19-net