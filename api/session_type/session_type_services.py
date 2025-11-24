from api.session_type.session_type_pydantic import *
from api.services_helpers import ensure_session_type_exists, ensure_session_type_unique
from api.session_type.session_type_DAL import SessionTypeDAL
from fastapi import HTTPException, Request

from config.logging_config import configure_logging

# Create logger object
logger = configure_logging()


class SessionTypeService:
    async def _create_new_session_type(self, body: CreateSessionType, request: Request, db) -> ShowSessionTypeWithHATEOAS:
        async with db as session:
            async with session.begin():
                session_type_dal = SessionTypeDAL(session)
                try:
                    if not await ensure_session_type_unique(session_type_dal, body.name):
                        raise HTTPException(status_code=400, detail=f"Тип сессии с именем '{body.name}' уже существует")

                    session_type = await session_type_dal.create_session_type(
                        name=body.name
                    )
                    session_type_name = session_type.name
                    session_type_pydantic = ShowSessionType.model_validate(session_type, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/session-types/search/by_name/{session_type_name}',
                        "update": f'{api_base_url}/session-types/update',
                        "delete": f'{api_base_url}/session-types/delete/{session_type_name}',
                        "session_types": f'{api_base_url}/session-types',
                        "sessions": f'{api_base_url}/sessions/search/by_type/{session_type_name}'
                    }

                    return ShowSessionTypeWithHATEOAS(session_type=session_type_pydantic, links=hateoas_links)

                except HTTPException:
                    await session.rollback()
                    raise
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Неожиданная ошибка при создании типа сессии '{body.name}': {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_session_type_by_name(self, name: str, request: Request, db) -> ShowSessionTypeWithHATEOAS:
        async with db as session:
            async with session.begin():
                session_type_dal = SessionTypeDAL(session)
                try:
                    session_type = await session_type_dal.get_session_type(name)
                    if not session_type:
                        raise HTTPException(status_code=404, detail=f"Тип сессии с именем '{name}' не найден")
                    session_type_pydantic = ShowSessionType.model_validate(session_type, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/session-types/search/by_name/{name}',
                        "update": f'{api_base_url}/session-types/update',
                        "delete": f'{api_base_url}/session-types/delete/{name}',
                        "session_types": f'{api_base_url}/session-types',
                        "sessions": f'{api_base_url}/sessions/search/by_type/{name}'
                    }

                    return ShowSessionTypeWithHATEOAS(session_type=session_type_pydantic, links=hateoas_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение типа сессии отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_all_session_types(self, page: int, limit: int, request: Request, db) -> ShowSessionTypeListWithHATEOAS:
        async with db as session:
            async with session.begin():
                session_type_dal = SessionTypeDAL(session)
                try:
                    session_types = await session_type_dal.get_all_session_types(page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    session_types_with_hateoas = []
                    for session_type in session_types:
                        session_type_pydantic = ShowSessionType.model_validate(session_type, from_attributes=True)
                        session_type_name = session_type.name
                        session_type_links = {
                            "self": f'{api_base_url}/session-types/search/by_name/{session_type_name}',
                            "update": f'{api_base_url}/session-types/update',
                            "delete": f'{api_base_url}/session-types/delete/{session_type_name}',
                            "session_types": f'{api_base_url}/session-types',
                            "sessions": f'{api_base_url}/sessions/search/by_type/{session_type_name}'
                        }
                        session_type_with_links = ShowSessionTypeWithHATEOAS(session_type=session_type_pydantic, links=session_type_links)
                        session_types_with_hateoas.append(session_type_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/session-types/search?page={page}&limit={limit}',
                        "create": f'{api_base_url}/session-types/create'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowSessionTypeListWithHATEOAS(session_types=session_types_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение типов сессий отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _delete_session_type(self, name: str, request: Request, db) -> ShowSessionTypeWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    session_type_dal = SessionTypeDAL(session)
                    if not await ensure_session_type_exists(session_type_dal, name):
                        raise HTTPException(status_code=404, detail=f"Тип сессии с именем '{name}' не найден")

                    session_type = await session_type_dal.delete_session_type(name)
                    if not session_type:
                        raise HTTPException(status_code=404, detail=f"Тип сессии с именем '{name}' не найден")

                    session_type_pydantic = ShowSessionType.model_validate(session_type, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "session_types": f'{api_base_url}/session-types',
                        "create": f'{api_base_url}/session-types/create'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowSessionTypeWithHATEOAS(session_type=session_type_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при удалении типа сессии '{name}': {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении типа сессии.")


    async def _update_session_type(self, body: UpdateSessionType, request: Request, db) -> ShowSessionTypeWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    session_type_dal = SessionTypeDAL(session)

                    if not await ensure_session_type_exists(session_type_dal, body.name):
                        raise HTTPException(status_code=404, detail=f"Тип сессии с именем '{body.name}' не найден")

                    if body.new_name != body.name:
                        if not await ensure_session_type_unique(session_type_dal, body.new_name):
                            raise HTTPException(status_code=400, detail=f"Тип сессии с именем '{body.new_name}' уже существует")

                    session_type = await session_type_dal.update_session_type(tg_name=body.name, name=body.new_name)
                    if not session_type:
                        raise HTTPException(status_code=404, detail=f"Тип сессии с именем '{body.name}' не найден")

                    session_type_name = session_type.name
                    session_type_pydantic = ShowSessionType.model_validate(session_type, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/session-types/search/by_name/{session_type_name}',
                        "update": f'{api_base_url}/session-types/update',
                        "delete": f'{api_base_url}/session-types/delete/{session_type_name}',
                        "session_types": f'{api_base_url}/session-types',
                        "sessions": f'{api_base_url}/sessions/search/by_type/{session_type_name}'
                    }

                    return ShowSessionTypeWithHATEOAS(session_type=session_type_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.warning(f"Изменение данных о типе сессии отменено (Ошибка: {e})")
                raise e
