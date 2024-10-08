from sqlalchemy import create_engine, select, and_
from sqlalchemy.orm import Session
from typing import Tuple, List
from datetime import datetime

from .models import Base, create_infobase_item, create_schedule_item
from .models import InfobaseModel, ScheduleModel, ADVANCE_DELTA
from .models import (
    SCAN_TIME_DELTA,
    DELETE_DELTA,
    CONTINUE_DELTA,
    MIN_BEFORE_DELETE
)


DB_URL = 'sqlite:///db/database.db'
engine = create_engine(DB_URL, echo=True)


def create_db_and_tables() -> None:
    Base.metadata.create_all(engine)


def create_infobase_and_scedule(
) -> Tuple[InfobaseModel, ScheduleModel]:
    infobase = create_infobase_item()
    schedule = create_schedule_item(infobase.uuid, infobase.start_time)
    with Session(engine) as session:
        session.add(infobase)
        session.add(schedule)
        session.commit()
    return infobase, schedule


def get_continue_ids(dt: datetime) -> List[str]:
    ret = []
    with Session(engine) as session:
        stmt = select(ScheduleModel).where(
            and_(
                ScheduleModel.continue_time < str(dt),
                ScheduleModel.continue_time > str(dt - SCAN_TIME_DELTA)
            )
        )
        objects = session.scalars(statement=stmt).all()
        ret = [o.uuid for o in objects]

    return ret


def delete_expired_data(dt: datetime) -> int:
    amount: int = 0
    with Session(engine) as session:
        # из расписания выделяем записи, кторые нужно удалить
        objs = session.query(ScheduleModel).filter(
            ScheduleModel.delete_time < str(dt)
        ).all()
        amount = len(objs)
        for o in objs:
            # по uuid находим записи в infobase и устанавливаем статус в 2
            # - выключено
            session.query(InfobaseModel).filter(
                InfobaseModel.uuid == o.uuid
            ).update({'status': 2})
            # удаляем запист из Schedule
            session.delete(o)

        # фиксируем изменения
        session.commit()
    return amount


def extend_working_time(uid: str) -> None:
    with Session(engine) as session:
        obj = session.query(ScheduleModel).filter(
            ScheduleModel.uuid == uid
        ).one()

        # чего-то нашли?
        if obj:
            obj.continue_time = obj.continue_time + ADVANCE_DELTA
            obj.delete_time = obj.delete_time + ADVANCE_DELTA
        session.commit()


def get_active_infobases() -> List[str]:
    """
    Возвращает список иднетификаторов инфобаз
    """
    with Session(engine) as session:
        objs = session.query(InfobaseModel).filter(
            InfobaseModel.status == 1
        ).all()

        uuids = [o.uuid for o in objs]
        return uuids
