from api.stream.stream_pydantic import *
from api.services_helpers import  ensure_group_exists, ensure_stream_unique, ensure_subject_in_cycle_exists
from api.stream.stream_DAL import StreamDAL
from api.subject_in_cycle.subject_in_cycle_DAL import SubjectsInCycleDAL
from api.group.group_DAL import GroupDAL
from fastapi import HTTPException, Request

from config.logging_config import configure_logging

# Create logger object
logger = configure_logging()


class StreamService:
    async def _create_new_stream(self, body: CreateStream, request: Request, db) -> ShowStreamWithHATEOAS:
        async with db as session:
            async with session.begin():
                group_dal = GroupDAL(session)
                subject_in_cycle_dal = SubjectsInCycleDAL(session)
                stream_dal = StreamDAL(session)
                try:
                    if not await ensure_group_exists(group_dal, body.group_name):
                        raise HTTPException(status_code=404, detail=f"Группа с названием {body.group_name} не найдена")
                    if not await ensure_subject_in_cycle_exists(subject_in_cycle_dal, body.subject_id):
                        raise HTTPException(status_code=404, detail=f"Предмет в цикле с id {body.subject_id} не найден")

                    if not await ensure_stream_unique(stream_dal, body.stream_id, body.group_name, body.subject_id):
                        raise HTTPException(status_code=400, detail=f"Поток с id {body.stream_id}, группой {body.group_name} и предметом {body.subject_id} уже существует")

                    stream = await stream_dal.create_stream(
                        stream_id=body.stream_id,
                        group_name=body.group_name,
                        subject_id=body.subject_id
                    )
                    stream_id = stream.stream_id
                    group_name = stream.group_name
                    subject_id = stream.subject_id
                    
                    stream_dict = {
                        "stream_id": stream.stream_id,
                        "group_name": stream.group_name,
                        "subject_id": stream.subject_id,
                    }
                    stream_pydantic = ShowStream.model_validate(stream_dict)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/streams/search/by_composite_key/{stream_id}/{group_name}/{subject_id}',
                        "update": f'{api_base_url}/streams/update',
                        "delete": f'{api_base_url}/streams/delete/{stream_id}/{group_name}/{subject_id}',
                        "streams": f'{api_base_url}/streams',
                        "group": f'{api_base_url}/groups/search/by_group_name/{group_name}',
                        "subject": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_id}',
                        "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}' 
                    }

                    return ShowStreamWithHATEOAS(stream=stream_pydantic, links=hateoas_links)

                except HTTPException:
                    await session.rollback()
                    raise
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Неожиданная ошибка при создании потока: {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_stream_by_composite_key(self, stream_id: int, group_name: str, subject_id: int, request: Request, db) -> ShowStreamWithHATEOAS:
        async with db as session:
            async with session.begin():
                stream_dal = StreamDAL(session)
                try:
                    stream = await stream_dal.get_stream_by_composite_key(stream_id, group_name, subject_id)
                    if not stream:
                        raise HTTPException(status_code=404, detail=f"Поток с id {stream_id}, группой {group_name} и предметом {subject_id} не найден")

                    stream_dict = {
                        "stream_id": stream.stream_id,
                        "group_name": stream.group_name,
                        "subject_id": stream.subject_id,
                    }
                    stream_pydantic = ShowStream.model_validate(stream_dict)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/streams/search/by_composite_key/{stream_id}/{group_name}/{subject_id}',
                        "update": f'{api_base_url}/streams/update',
                        "delete": f'{api_base_url}/streams/delete/{stream_id}/{group_name}/{subject_id}',
                        "streams": f'{api_base_url}/streams',
                        "group": f'{api_base_url}/groups/search/by_group_name/{group_name}',
                        "subject": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_id}',
                        "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}'
                    }

                    return ShowStreamWithHATEOAS(stream=stream_pydantic, links=hateoas_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение потока {stream_id} для группы {group_name} и предмета {subject_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_streams_by_group(self, group_name: str, page: int, limit: int, request: Request, db) -> ShowStreamListWithHATEOAS:
        async with db as session:
            async with session.begin():
                group_dal = GroupDAL(session)
                stream_dal = StreamDAL(session)
                try:
                    if not await ensure_group_exists(group_dal, group_name):
                        raise HTTPException(status_code=404, detail=f"Группа с названием {group_name} не найдена")

                    streams = await stream_dal.get_streams_by_group(group_name, page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    streams_with_hateoas = []
                    for stream in streams:
                        stream_dict = {
                            "stream_id": stream.stream_id,
                            "group_name": stream.group_name,
                            "subject_id": stream.subject_id,
                        }
                        stream_pydantic = ShowStream.model_validate(stream_dict)
                        stream_id = stream.stream_id
                        subject_id = stream.subject_id
                        stream_links = {
                            "self": f'{api_base_url}/streams/search/by_composite_key/{stream_id}/{group_name}/{subject_id}',
                            "update": f'{api_base_url}/streams/update',
                            "delete": f'{api_base_url}/streams/delete/{stream_id}/{group_name}/{subject_id}',
                            "streams": f'{api_base_url}/streams',
                            "group": f'{api_base_url}/groups/search/by_group_name/{group_name}',
                            "subject": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_id}',
                            "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}'
                        }
                        stream_with_links = ShowStreamWithHATEOAS(stream=stream_pydantic, links=stream_links)
                        streams_with_hateoas.append(stream_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/streams/search/by_group/{group_name}?page={page}&limit={limit}',
                        "create": f'{api_base_url}/streams/create',
                        "group": f'{api_base_url}/groups/search/by_group_name/{group_name}'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowStreamListWithHATEOAS(streams=streams_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение потоков для группы {group_name} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_streams_by_subject(self, subject_id: int, page: int, limit: int, request: Request, db) -> ShowStreamListWithHATEOAS:
        async with db as session:
            async with session.begin():
                subject_in_cycle_dal = SubjectsInCycleDAL(session)
                stream_dal = StreamDAL(session)
                try:
                    if not await ensure_subject_in_cycle_exists(subject_in_cycle_dal, subject_id):
                        raise HTTPException(status_code=404, detail=f"Предмет в цикле с id {subject_id} не найден")

                    streams = await stream_dal.get_streams_by_subject(subject_id, page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    streams_with_hateoas = []
                    for stream in streams:
                        stream_dict = {
                            "stream_id": stream.stream_id,
                            "group_name": stream.group_name,
                            "subject_id": stream.subject_id,
                        }
                        stream_pydantic = ShowStream.model_validate(stream_dict)
                        stream_id = stream.stream_id
                        group_name = stream.group_name
                        stream_links = {
                            "self": f'{api_base_url}/streams/search/by_composite_key/{stream_id}/{group_name}/{subject_id}',
                            "update": f'{api_base_url}/streams/update',
                            "delete": f'{api_base_url}/streams/delete/{stream_id}/{group_name}/{subject_id}',
                            "streams": f'{api_base_url}/streams',
                            "group": f'{api_base_url}/groups/search/by_group_name/{group_name}',
                            "subject": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_id}',
                            "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}'
                        }
                        stream_with_links = ShowStreamWithHATEOAS(stream=stream_pydantic, links=stream_links)
                        streams_with_hateoas.append(stream_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/streams/search/by_subject/{subject_id}?page={page}&limit={limit}',
                        "create": f'{api_base_url}/streams/create',
                        "subject": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_id}'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowStreamListWithHATEOAS(streams=streams_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение потоков для предмета в цикле {subject_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_all_streams(self, page: int, limit: int, request: Request, db) -> ShowStreamListWithHATEOAS:
        async with db as session:
            async with session.begin():
                stream_dal = StreamDAL(session)
                try:
                    streams = await stream_dal.get_all_streams(page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    streams_with_hateoas = []
                    for stream in streams:
                        stream_dict = {
                            "stream_id": stream.stream_id,
                            "group_name": stream.group_name,
                            "subject_id": stream.subject_id,
                        }
                        stream_pydantic = ShowStream.model_validate(stream_dict)
                        stream_id = stream.stream_id
                        group_name = stream.group_name
                        subject_id = stream.subject_id
                        stream_links = {
                            "self": f'{api_base_url}/streams/search/by_composite_key/{stream_id}/{group_name}/{subject_id}',
                            "update": f'{api_base_url}/streams/update',
                            "delete": f'{api_base_url}/streams/delete/{stream_id}/{group_name}/{subject_id}',
                            "streams": f'{api_base_url}/streams',
                            "group": f'{api_base_url}/groups/search/by_group_name/{group_name}',
                            "subject": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_id}',
                            "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}'
                        }
                        stream_with_links = ShowStreamWithHATEOAS(stream=stream_pydantic, links=stream_links)
                        streams_with_hateoas.append(stream_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/streams/search?page={page}&limit={limit}',
                        "create": f'{api_base_url}/streams/create'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowStreamListWithHATEOAS(streams=streams_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение потоков отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _delete_stream(self, stream_id: int, group_name: str, subject_id: int, request: Request, db) -> ShowStreamWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    stream_dal = StreamDAL(session)

                    stream = await stream_dal.get_stream_by_composite_key(stream_id, group_name, subject_id)
                    if not stream:
                        raise HTTPException(status_code=404, detail=f"Поток с id {stream_id}, группой {group_name} и предметом {subject_id} не найден")

                    deleted_stream = await stream_dal.delete_stream(stream_id, group_name, subject_id)
                    
                    if not deleted_stream:
                        raise HTTPException(status_code=404, detail=f"Поток с id {stream_id}, группой {group_name} и предметом {subject_id} не найден")

                    stream_dict = {
                        "stream_id": deleted_stream.stream_id,
                        "group_name": deleted_stream.group_name,
                        "subject_id": deleted_stream.subject_id,
                    }
                    stream_pydantic = ShowStream.model_validate(stream_dict)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "streams": f'{api_base_url}/streams',
                        "create": f'{api_base_url}/streams/create'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowStreamWithHATEOAS(stream=stream_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при удалении потока {stream_id} для группы {group_name} и предмета {subject_id}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении потока.")


    async def _update_stream(self, body: UpdateStream, request: Request, db) -> ShowStreamWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["stream_id", "group_name", "subject_id", "new_stream_id", "new_group_name", "new_subject_id"]}

                    target_stream_id = body.stream_id
                    target_group_name = body.group_name
                    target_subject_id = body.subject_id
                    if body.new_stream_id is not None:
                        update_data["stream_id"] = body.new_stream_id
                        target_stream_id = body.new_stream_id
                    if body.new_group_name is not None:
                        update_data["group_name"] = body.new_group_name
                        target_group_name = body.new_group_name
                    if body.new_subject_id is not None:
                        update_data["subject_id"] = body.new_subject_id
                        target_subject_id = body.new_subject_id

                    if "group_name" in update_data:
                        group_dal = GroupDAL(session)
                        if not await ensure_group_exists(group_dal, update_data["group_name"]):
                            raise HTTPException(status_code=404, detail=f"Группа с названием {update_data['group_name']} не найдена")
                    if "subject_id" in update_data:
                        subject_in_cycle_dal = SubjectsInCycleDAL(session)
                        if not await ensure_subject_in_cycle_exists(subject_in_cycle_dal, update_data["subject_id"]):
                            raise HTTPException(status_code=404, detail=f"Предмет в цикле с id {update_data['subject_id']} не найден")

                    stream_dal = StreamDAL(session)

                    stream = await stream_dal.get_stream_by_composite_key(body.stream_id, body.group_name, body.subject_id)
                    if not stream:
                        raise HTTPException(status_code=404, detail=f"Поток с id {body.stream_id}, группой {body.group_name} и предметом {body.subject_id} не найден")

                    if (target_stream_id, target_group_name, target_subject_id) != (body.stream_id, body.group_name, body.subject_id):
                        if not await ensure_stream_unique(stream_dal, target_stream_id, target_group_name, target_subject_id):
                            raise HTTPException(status_code=400, detail=f"Поток с id {target_stream_id}, группой {target_group_name} и предметом {target_subject_id} уже существует")

                    updated_stream = await stream_dal.update_stream(target_stream_id=body.stream_id, target_group_name=body.group_name, target_subject_id=body.subject_id, **update_data)
                    if not updated_stream:
                        raise HTTPException(status_code=404, detail=f"Поток с id {body.stream_id}, группой {body.group_name} и предметом {body.subject_id} не найден")

                    stream_id = updated_stream.stream_id
                    group_name = updated_stream.group_name
                    subject_id = updated_stream.subject_id
                    
                    stream_dict = {
                        "stream_id": updated_stream.stream_id,
                        "group_name": updated_stream.group_name,
                        "subject_id": updated_stream.subject_id,
                    }
                    stream_pydantic = ShowStream.model_validate(stream_dict)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/streams/search/by_composite_key/{stream_id}/{group_name}/{subject_id}',
                        "update": f'{api_base_url}/streams/update',
                        "delete": f'{api_base_url}/streams/delete/{stream_id}/{group_name}/{subject_id}',
                        "streams": f'{api_base_url}/streams',
                        "group": f'{api_base_url}/groups/search/by_group_name/{group_name}',
                        "subject": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_id}',
                        "sessions": f'{api_base_url}/sessions/search/by_group/{group_name}'
                    }

                    return ShowStreamWithHATEOAS(stream=stream_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.warning(f"Изменение данных о потоке отменено (Ошибка: {e})")
                raise e
            