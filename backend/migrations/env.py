import os
from alembic import context
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from backend.app.models import metadata

config = context.config
url = os.environ.get('DATABASE_URL', config.get_main_option('sqlalchemy.url'))
if context.is_offline_mode():
    context.configure(url=url, target_metadata=metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    with create_engine(url, poolclass=NullPool).connect() as connection:
        context.configure(connection=connection, target_metadata=metadata)
        with context.begin_transaction():
            context.run_migrations()
