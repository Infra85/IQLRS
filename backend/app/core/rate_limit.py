import hashlib
import time
from fastapi import Depends, HTTPException, Request
from sqlalchemy import case, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.rate_limit import RateLimit


def limit_requests(scope: str, maximum: int, seconds: int = 60):
    def check(request: Request, db: Session = Depends(get_db)):
        # Trust forwarded client addresses only through Uvicorn's configured trusted proxy.
        host = request.client.host if request.client else 'unknown'
        key = hashlib.sha256(f'{scope}:{host}'.encode()).hexdigest()
        now = int(time.time())
        window = now // seconds * seconds
        stmt = insert(RateLimit).values(key=key, window_start=window, count=1)
        stmt = stmt.on_conflict_do_update(index_elements=[RateLimit.key], set_={
            'window_start': window,
            'count': case((RateLimit.window_start == window, RateLimit.count + 1), else_=1),
        }).returning(RateLimit.count)
        with Session(bind=db.get_bind()) as counter_db:
            count = counter_db.execute(stmt).scalar_one()
            counter_db.execute(delete(RateLimit).where(RateLimit.window_start < now-86400))
            counter_db.commit()
        if count > maximum:
            raise HTTPException(429, 'Too many requests. Please try again later.', headers={'Retry-After': str(seconds)})
    return check
