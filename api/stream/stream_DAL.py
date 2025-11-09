from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Stream
from config.decorators import log_exceptions


class StreamDAL:
    """Data Access Layer for operating stream info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_stream(self, stream_id: int, group_name: str, subject_id: int) -> Stream:
        new_stream = Stream(
            stream_id=stream_id,
            group_name=group_name,
            subject_id=subject_id
        )
        self.db_session.add(new_stream)
        await self.db_session.flush()
        return new_stream

    @log_exceptions
    async def delete_stream(self, stream_id: int, group_name: str, subject_id: int) -> Stream | None:
        query = delete(Stream).where(
            (Stream.stream_id == stream_id) &
            (Stream.group_name == group_name) &
            (Stream.subject_id == subject_id)
        ).returning(Stream)
        res = await self.db_session.execute(query)
        deleted_stream = res.scalar_one_or_none()
        return deleted_stream

    @log_exceptions
    async def get_all_streams(self, page: int, limit: int) -> list[Stream]:
        if page == 0:
            query = select(Stream).order_by(Stream.stream_id.asc())
        else:
            query = select(Stream).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        streams = list(result.scalars().all())
        return streams

    @log_exceptions
    async def get_stream_by_composite_key(self, stream_id: int, group_name: str, subject_id: int) -> Stream | None:
        query = select(Stream).where(
            (Stream.stream_id == stream_id) &
            (Stream.group_name == group_name) &
            (Stream.subject_id == subject_id)
        )
        res = await self.db_session.execute(query)
        stream_row = res.scalar_one_or_none()
        return stream_row

    @log_exceptions
    async def get_streams_by_group(self, group_name: str, page: int, limit: int) -> list[Stream]:
        if page == 0:
            query = select(Stream).where(Stream.group_name == group_name).order_by(Stream.stream_id.asc())
        else:
            query = select(Stream).where(Stream.group_name == group_name).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        streams = list(result.scalars().all())
        return streams if streams is not None else []

    @log_exceptions
    async def get_streams_by_subject(self, subject_id: int, page: int, limit: int) -> list[Stream]:
        if page == 0:
            query = select(Stream).where(Stream.subject_id == subject_id).order_by(Stream.stream_id.asc())
        else:
            query = select(Stream).where(Stream.subject_id == subject_id).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        streams = list(result.scalars().all())
        return streams if streams is not None else []

    @log_exceptions
    async def update_stream(self, target_stream_id: int, target_group_name: str, target_subject_id: int, **kwargs) -> Stream | None:
        query = update(Stream).where(
            (Stream.stream_id == target_stream_id) &
            (Stream.group_name == target_group_name) &
            (Stream.subject_id == target_subject_id)
        ).values(**kwargs).returning(Stream)
        res = await self.db_session.execute(query)
        updated_stream = res.scalar_one_or_none()
        return updated_stream
