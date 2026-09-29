import os
from pathlib import Path
from contextlib import contextmanager
from datetime import date
from functools import lru_cache
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Text, CheckConstraint, select, func, update, delete
from sqlalchemy.pool import NullPool

ROOT = Path(__file__).resolve().parent.parent
DB = Path(os.environ.get('TODO_DB', ROOT / 'data' / 'todo.sqlite3'))
metadata = MetaData()
items = Table('items', metadata,
    Column('id', Integer, primary_key=True),
    Column('kind', Text, nullable=False), Column('title', Text, nullable=False),
    Column('body', Text, nullable=False, server_default=''),
    Column('done', Integer, nullable=False, server_default='0'),
    Column('due_date', Text), Column('position', Integer, nullable=False),
    CheckConstraint("kind IN ('task','note')"))

def settings():
    url = os.environ.get('DATABASE_URL', '')
    if os.environ.get('VERCEL') and not url:
        raise HTTPException(503, 'Setup incomplete. Configure DATABASE_URL.')
    if url and not url.startswith(('postgresql://', 'postgres://', 'postgresql+psycopg://')):
        raise HTTPException(503, 'DATABASE_URL must be a PostgreSQL connection string.')
    return url

@lru_cache(maxsize=8)
def engine_for(url):
    engine = create_engine(url, poolclass=NullPool, connect_args={'connect_timeout':10} if url.startswith('postgresql') else {'timeout':10})
    with engine.begin() as conn:
        if engine.dialect.name == 'postgresql':
            conn.exec_driver_sql('SELECT pg_advisory_xact_lock(748201)')
        metadata.create_all(conn)
    return engine

@contextmanager
def database():
    url = settings()
    if url:
        url = url.replace('postgres://','postgresql+psycopg://',1).replace('postgresql://','postgresql+psycopg://',1)
    else:
        DB.parent.mkdir(parents=True, exist_ok=True)
        url = 'sqlite:///' + DB.as_posix()
    engine = engine_for(url)
    with engine.connect() as conn:
        # Serialize writes and reordering across workers, including simultaneous adds.
        if engine.dialect.name == 'sqlite':
            conn.exec_driver_sql('BEGIN IMMEDIATE')
        else:
            conn.begin()
            conn.exec_driver_sql('SELECT pg_advisory_xact_lock(748202)')
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

app = FastAPI(title='Little List API', docs_url=None if os.environ.get('VERCEL') else '/docs', redoc_url=None, openapi_url=None if os.environ.get('VERCEL') else '/openapi.json')

@app.middleware('http')
async def response_headers(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'same-origin'
    return response

class Item(BaseModel):
    kind: Literal['task', 'note'] = 'task'
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(default='', max_length=20000)
    done: bool = False
    due_date: date | None = None

    @field_validator('title')
    @classmethod
    def clean_title(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('Please enter a title')
        return value

class Order(BaseModel):
    kind: Literal['task', 'note']
    ids: list[int]

def values(item):
    return {**item.model_dump(), 'done':int(item.done), 'due_date':item.due_date.isoformat() if item.due_date else None}

@app.get('/api/items')
def list_items():
    with database() as conn:
        return [dict(row) for row in conn.execute(select(items).order_by(items.c.position, items.c.id)).mappings()]

@app.post('/api/items', status_code=201)
def create_item(item: Item):
    with database() as conn:
        pos = conn.scalar(select(func.coalesce(func.max(items.c.position), -1)+1).where(items.c.kind == item.kind))
        result = conn.execute(items.insert().values(**values(item), position=pos))
        return dict(conn.execute(select(items).where(items.c.id == result.inserted_primary_key[0])).mappings().one())

@app.put('/api/order')
def reorder(order: Order):
    with database() as conn:
        existing = set(conn.scalars(select(items.c.id).where(items.c.kind == order.kind)))
        if len(order.ids) != len(set(order.ids)) or set(order.ids) != existing:
            raise HTTPException(409, 'The list changed. Refresh and try again.')
        for position, item_id in enumerate(order.ids):
            conn.execute(update(items).where(items.c.id == item_id).values(position=position))
    return {'ok': True}

@app.put('/api/items/{item_id}')
def update_item(item_id: int, item: Item):
    with database() as conn:
        row = conn.execute(select(items).where(items.c.id == item_id)).mappings().first()
        if not row:
            raise HTTPException(404, 'Item not found')
        if row['kind'] != item.kind:
            raise HTTPException(400, 'Item type cannot be changed')
        conn.execute(update(items).where(items.c.id == item_id).values(**values(item)))
        return dict(conn.execute(select(items).where(items.c.id == item_id)).mappings().one())

@app.delete('/api/items/{item_id}', status_code=204)
def delete_item(item_id: int):
    with database() as conn:
        if conn.execute(delete(items).where(items.c.id == item_id)).rowcount == 0:
            raise HTTPException(404, 'Item not found')

DIST = ROOT / 'frontend' / 'dist'
if DIST.exists():
    app.mount('/', StaticFiles(directory=DIST, html=True), name='frontend')
