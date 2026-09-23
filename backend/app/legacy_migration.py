"""Preserve the integer-ID schema while copying its data into the UUID models.

All DDL and inserts run in the caller's single transaction. The original tables
remain in an archive schema, including fields no longer represented by models.
"""
from collections import defaultdict
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5
from sqlalchemy import MetaData, Table, inspect, select, text
from app.core.database import Base
from app.services.curriculum import AUTHOR_ID

RENAMES = {
    'users': {'password_hash': 'hashed_password'},
    'circuit_gates': {'qubit_position': 'qubit', 'gate_order': 'position'},
    'simulation_runs': {'backend': 'simulator', 'started_at': 'created_at'},
    'module_progress': {'completion_pct': 'progress_percent', 'last_accessed_at': 'updated_at'},
    'assessment_attempts': {'submitted_at': 'completed_at'},
    'ai_messages': {'sender_type': 'role', 'message': 'content', 'context_data': 'message_metadata'},
    'user_gamification': {'current_streak': 'streak_days', 'longest_streak': 'streak_days'},
    'badges': {'icon_url': 'icon'},
    'shared_resources': {'resource_type': 'kind', 'resource_data': 'payload'},
}


def legacy_id(table, value):
    return uuid5(NAMESPACE_URL, f'https://iqlrs/legacy/{table}/{value}')


def migrate_legacy(connection):
    inspector = inspect(connection)
    source_schema = connection.execute(text('SELECT current_schema()')).scalar_one()
    archive = source_schema + '_legacy_v1'
    if inspector.has_schema(archive):
        raise RuntimeError('Legacy archive already exists; investigate before migrating. No data changed.')
    tables = {name: Table(name, MetaData(), autoload_with=connection, schema=source_schema)
              for name in inspector.get_table_names() if name in Base.metadata.tables}
    rows = {name: [dict(row) for row in connection.execute(select(table)).mappings()] for name, table in tables.items()}
    # Move all original tables and indexes together. FKs continue referencing the archive.
    quote = connection.dialect.identifier_preparer.quote
    connection.execute(text(f'CREATE SCHEMA {quote(archive)}'))
    connection.execute(text(f'REVOKE ALL ON SCHEMA {quote(archive)} FROM PUBLIC'))
    for name in tables:
        connection.execute(text(f'ALTER TABLE {quote(source_schema)}.{quote(name)} SET SCHEMA {quote(archive)}'))
    Base.metadata.create_all(connection)
    question_order = defaultdict(int)
    author_inserted = False
    for target in Base.metadata.sorted_tables:
        name = target.name
        for old in rows.get(name, []):
            values = {}
            for column in target.columns:
                source = RENAMES.get(name, {}).get(column.name, column.name)
                if column.foreign_keys:
                    if source in old and old[source] is not None:
                        foreign = next(iter(column.foreign_keys)).column.table.name
                        values[column.name] = legacy_id(foreign, old[source])
                elif column.primary_key:
                    values[column.name] = legacy_id(name, old['id'])
                elif source in old:
                    value = old[source]
                    if isinstance(value, datetime) and value.tzinfo is None:
                        value = value.replace(tzinfo=timezone.utc)
                    values[column.name] = value
            if name == 'users':
                values.update(otp_code=None, otp_expires_at=None, otp_attempts=0)
            if name == 'courses':
                values['created_by'] = AUTHOR_ID
            if name == 'circuit_versions':
                circuit = next(c for c in rows['circuits'] if c['id'] == old['circuit_id'])
                values['created_by'] = legacy_id('users', circuit['user_id'])
            if name == 'simulation_runs':
                values['execution_time_ms'] = round(old['execution_time']*1000) if old.get('execution_time') is not None else None
                if old.get('status') == 'completed':
                    values['completed_at'] = values.get('started_at')
            if name == 'module_progress':
                values['status'] = 'completed' if old.get('completed') else 'in_progress'
                if old.get('completed'):
                    values['completed_at'] = values.get('last_accessed_at')
            if name == 'questions':
                question_order[old['assessment_id']] += 1
                values['question_order'] = question_order[old['assessment_id']]
            if name == 'assessment_attempts':
                maximum = sum(q.get('points', 1) for q in rows.get('questions', []) if q['assessment_id'] == old['assessment_id'])
                values['max_score'] = maximum
                values['percentage'] = 100*old.get('score', 0)/maximum if maximum else 0
                values['status'] = 'submitted' if old.get('completed') else 'in_progress'
            if name == 'code_submissions':
                values['passed'] = old.get('status') == 'passed'
            # Missing new fields use declared model defaults; nullable fields stay NULL.
            for column in target.columns:
                if column.name in values and values[column.name] is None and not column.nullable and column.default:
                    del values[column.name]
                if column.name not in values and not column.nullable and not column.default and not column.server_default:
                    raise RuntimeError(f'Legacy migration needs a value for {name}.{column.name}; transaction rolled back.')
            connection.execute(target.insert().values(**values))
        if name == 'users' and not author_inserted:
            connection.execute(target.insert().values(user_id=AUTHOR_ID, email='curriculum@iqlrs.invalid', name='IQLRS Curriculum', email_verified=False))
            author_inserted = True
    print(f'Legacy records copied to UUID models; original tables retained in {archive}.')
