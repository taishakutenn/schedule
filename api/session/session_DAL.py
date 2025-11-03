from sqlalchemy import Date, select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Session
from config.decorators import log_exceptions


class SessionDAL:
    """Data Access Layer for operating session info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_session(
        self,
        session_number: int,
        session_date: Date,
        teacher_in_plan: int,
        session_type: str,
        cabinet_number: int | None = None,
        building_number: int | None = None
    ) -> Session:
        new_session = Session(
            session_number=session_number,
            date=session_date, 
            teacher_in_plan=teacher_in_plan,
            session_type=session_type,
            cabinet_number=cabinet_number,
            building_number=building_number
        )
        self.db_session.add(new_session)
        await self.db_session.flush()
        return new_session

    @log_exceptions
    async def delete_session(self, session_number: int, session_date: Date, teacher_in_plan: int) -> Session | None:
        query = delete(Session).where(
            (Session.session_number == session_number) &
            (Session.date == session_date) & 
            (Session.teacher_in_plan == teacher_in_plan)
        ).returning(Session)
        res = await self.db_session.execute(query)
        deleted_session = res.scalar_one_or_none()
        return deleted_session

    @log_exceptions
    async def get_all_sessions(self, page: int, limit: int) -> list[Session]:
        if page == 0:
            query = select(Session).order_by(Session.date.asc(), Session.session_number.asc()) 
        else:
            query = select(Session).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        sessions = list(result.scalars().all())
        return sessions

    @log_exceptions
    async def get_session_by_composite_key(self, session_number: int, session_date: Date, teacher_in_plan: int) -> Session | None: 
        query = select(Session).where(
            (Session.session_number == session_number) &
            (Session.date == session_date) & 
            (Session.teacher_in_plan == teacher_in_plan)
        )
        res = await self.db_session.execute(query)
        session_row = res.scalar_one_or_none()
        return session_row

    @log_exceptions
    async def get_sessions_by_plan(self, teacher_in_plan_id: int, page: int, limit: int) -> list[Session]:
        if page == 0:
            query = select(Session).where(Session.teacher_in_plan == teacher_in_plan_id).order_by(Session.date.asc(), Session.session_number.asc()) 
        else:
            query = select(Session).where(Session.teacher_in_plan == teacher_in_plan_id).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        sessions = list(result.scalars().all())
        return sessions if sessions is not None else []

    @log_exceptions
    async def get_sessions_by_date(self, session_date: Date, page: int, limit: int) -> list[Session]: 
        if page == 0:
            query = select(Session).where(Session.date == session_date).order_by(Session.session_number.asc()) 
        else:
            query = select(Session).where(Session.date == session_date).offset((page - 1) * limit).limit(limit) 
        result = await self.db_session.execute(query)
        sessions = list(result.scalars().all())
        return sessions if sessions is not None else []

    @log_exceptions
    async def get_sessions_by_type(self, session_type: str, page: int, limit: int) -> list[Session]:
        if page == 0:
            query = select(Session).where(Session.session_type == session_type).order_by(Session.date.asc(), Session.session_number.asc()) 
        else:
            query = select(Session).where(Session.session_type == session_type).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        sessions = list(result.scalars().all())
        return sessions if sessions is not None else []
    
    @log_exceptions
    async def get_session_by_cabinet_and_time(self, cabinet_number: int, building_number: int, session_date: Date, session_number: int) -> Session | None:
        query = select(Session).where(
            (Session.cabinet_number == cabinet_number) &
            (Session.building_number == building_number) &
            (Session.date == session_date) &
            (Session.session_number == session_number)
        )
        res = await self.db_session.execute(query)
        session_row = res.scalar_one_or_none()
        return session_row

    @log_exceptions
    async def get_sessions_by_cabinet(self, cabinet_number: int, building_number: int, page: int, limit: int) -> list[Session]:
        if page == 0:
            query = select(Session).where(
                (Session.cabinet_number == cabinet_number) &
                (Session.building_number == building_number)
            ).order_by(Session.date.asc(), Session.session_number.asc()) 
        else:
            query = select(Session).where(
                (Session.cabinet_number == cabinet_number) &
                (Session.building_number == building_number)
            ).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        sessions = list(result.scalars().all())
        return sessions if sessions is not None else []

    @log_exceptions
    async def update_session(self, target_session_number: int, target_session_date: Date, target_teacher_in_plan: int, **kwargs) -> Session | None: 
        query = update(Session).where(
            (Session.session_number == target_session_number) &
            (Session.date == target_session_date) &
            (Session.teacher_in_plan == target_teacher_in_plan)
        ).values(**kwargs).returning(Session)
        res = await self.db_session.execute(query)
        updated_session = res.scalar_one_or_none()
        return updated_session
