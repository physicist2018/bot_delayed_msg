from datetime import datetime, timedelta


from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Integer

import uuid


# период продления работы БД
ADVANCE_DELTA = timedelta(minutes=20)

# задержка от момента создания БД
# до вопроса о продлении
CONTINUE_DELTA = timedelta(minutes=10)

# задержка от момента создания БД
# до удаления записи
DELETE_DELTA = timedelta(minutes=15)

# задержка перед удалением после предупреждения
MIN_BEFORE_DELETE = timedelta(minutes=5)

# период опроса БД
SCAN_TIME_DELTA = timedelta(minutes=1)


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)
    pass


class InfobaseModel(Base):
    __tablename__ = 'infobase'
    uuid: Mapped[str] = mapped_column(
        String(30),
        default=str(uuid.uuid1())
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=False)
    )
    status: Mapped[Integer] = mapped_column(Integer, default=1)


class ScheduleModel(Base):
    __tablename__ = 'schedule'
    uuid: Mapped[str] = mapped_column(String(30), nullable=False)
    continue_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False
    )
    delete_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False
    )


def create_infobase_item() -> InfobaseModel:
    ret = InfobaseModel(
        uuid=str(uuid.uuid1()),
        start_time=datetime.today()
    )
    return ret


def create_schedule_item(uid: str, dt: datetime) -> ScheduleModel:
    return ScheduleModel(
        uuid=uid,
        continue_time=dt+CONTINUE_DELTA,
        delete_time=dt+DELETE_DELTA
    )
