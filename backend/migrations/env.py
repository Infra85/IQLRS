"""Alembic bridge after the existing version-1 schema bootstrap."""

from alembic import context

connection = context.config.attributes.get("connection")
if connection is None:
    raise RuntimeError("Run migrations with python -m app.migrate")
context.configure(connection=connection)
with context.begin_transaction():
    context.run_migrations()
