from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime
import datetime as dt
from settings import settings

Base = declarative_base()

def utcnow():
    return dt.datetime.utcnow()

class CallLog(Base):
    __tablename__ = "call_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    call_sid = Column(String(64), unique=True, index=True)
    from_number = Column(String(32))
    timestamp = Column(DateTime, default=utcnow)

    caller_name = Column(String(128))
    company = Column(String(128), nullable=True)
    reason = Column(Text, nullable=True)

    caller_type = Column(String(32))         # recruiter | family | friend | promotion | unknown
    priority = Column(String(16))            # high | medium | low
    action = Column(String(32))              # connect_now | take_message
    urgency_minutes = Column(Integer, nullable=True)

    connected = Column(Boolean, default=False)
    voicemail_url = Column(String(256), nullable=True)
    recording_url = Column(String(256), nullable=True)
    transcript = Column(Text, nullable=True)

    notes = Column(Text, nullable=True)

engine = create_async_engine(settings.database_url, future=True, echo=False)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def save_call(session: AsyncSession, **kwargs):
    log = CallLog(**kwargs)
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log

async def update_call(session: AsyncSession, call_sid: str, **kwargs):
    from sqlalchemy import select
    result = await session.execute(select(CallLog).where(CallLog.call_sid == call_sid))
    log = result.scalars().first()
    if log:
        for k, v in kwargs.items():
            setattr(log, k, v)
        await session.commit()
        await session.refresh(log)
    return log

async def get_call(session: AsyncSession, call_sid: str):
    from sqlalchemy import select
    result = await session.execute(select(CallLog).where(CallLog.call_sid == call_sid))
    return result.scalars().first()
