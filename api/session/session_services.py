from api.session.session_pydantic import *
from api.services_helpers import ensure_cabinet_exists, ensure_session_type_exists, ensure_teacher_in_plan_exists
from api.session.session_DAL import SessionDAL
from api.teacher_in_plan.teacher_in_plan_DAL import TeacherInPlanDAL
from api.session_type.session_type_DAL import SessionTypeDAL
from api.cabinet.cabinet_DAL import CabinetDAL
from fastapi import HTTPException, Request

from config.logging_config import configure_logging

# Create logger object
logger = configure_logging()


class SessionService:
    async def _create_new_session(self, body: CreateSession, request: Request, db) -> ShowSessionWithHATEOAS:
        async with db as session:
            async with session.begin():
                session_dal = SessionDAL(session)
                teacher_in_plan_dal = TeacherInPlanDAL(session)
                session_type_dal = SessionTypeDAL(session)
                cabinet_dal = CabinetDAL(session)
                try:
                    if not await ensure_teacher_in_plan_exists(teacher_in_plan_dal, body.teacher_in_plan):
                        raise HTTPException(status_code=404, detail=f"Запись в расписании преподавателя с id {body.teacher_in_plan} не найдена")
                    if not await ensure_session_type_exists(session_type_dal, body.session_type):
                        raise HTTPException(status_code=404, detail=f"Тип занятия {body.session_type} не найден")
                    
                    if body.cabinet_number is not None and body.building_number is not None:
                        cabinet_exists = await cabinet_dal.get_cabinet_by_number_and_building(body.building_number, body.cabinet_number)
                        if not cabinet_exists:
                            raise HTTPException(status_code=404, detail=f"Кабинет {body.cabinet_number} в здании {body.building_number} не найден")

                    existing_session = await session_dal.get_session_by_composite_key(body.session_number, body.session_date, body.teacher_in_plan)
                    if existing_session:
                        raise HTTPException(status_code=400, detail=f"Занятие с номером {body.session_number}, датой {body.session_date} и записью в расписании преподавателя {body.teacher_in_plan} уже существует")

                    session_obj = await session_dal.create_session(
                        session_number=body.session_number,
                        session_date=body.session_date,
                        teacher_in_plan=body.teacher_in_plan,
                        session_type=body.session_type,
                        cabinet_number=body.cabinet_number,
                        building_number=body.building_number
                    )
                    session_number = session_obj.session_number
                    session_date = session_obj.date 
                    teacher_in_plan_id = session_obj.teacher_in_plan
                    
                    session_dict = {
                        "session_number": session_obj.session_number,
                        "session_date": session_obj.date,
                        "teacher_in_plan": session_obj.teacher_in_plan,
                        "session_type": session_obj.session_type,
                        "cabinet_number": session_obj.cabinet_number,
                        "building_number": session_obj.building_number,
                    }
                    session_pydantic = ShowSession.model_validate(session_dict)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/sessions/search/by_composite_key/{session_number}/{session_date}/{teacher_in_plan_id}',
                        "update": f'{api_base_url}/sessions/update',
                        "delete": f'{api_base_url}/sessions/delete/{session_number}/{session_date}/{teacher_in_plan_id}',
                        "sessions": f'{api_base_url}/sessions',
                        "plan": f'{api_base_url}/teachers_in_plans/search/by_id/{body.teacher_in_plan}',
                        "type": f'{api_base_url}/session-types/search/by_name/{body.session_type}',
                        "cabinet": f'{api_base_url}/cabinets/search/by_building_and_number/{body.building_number}/{body.cabinet_number}' if body.cabinet_number and body.building_number else None
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowSessionWithHATEOAS(session=session_pydantic, links=hateoas_links)

                except HTTPException:
                    await session.rollback()
                    raise
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Неожиданная ошибка при создании занятия: {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_session_by_composite_key(self, session_number: int, session_date: date, teacher_in_plan: int, request: Request, db) -> ShowSessionWithHATEOAS:
        async with db as session:
            async with session.begin():
                session_dal = SessionDAL(session)
                try:
                    session_obj = await session_dal.get_session_by_composite_key(session_number, session_date, teacher_in_plan)
                    if not session_obj:
                        raise HTTPException(status_code=404, detail=f"Занятие с номером {session_number}, датой {session_date} и записью в расписании преподавателя {teacher_in_plan} не найдено")

                    session_dict = {
                        "session_number": session_obj.session_number,
                        "session_date": session_obj.date,
                        "teacher_in_plan": session_obj.teacher_in_plan,
                        "session_type": session_obj.session_type,
                        "cabinet_number": session_obj.cabinet_number,
                        "building_number": session_obj.building_number,
                    }
                    session_pydantic = ShowSession.model_validate(session_dict)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/sessions/search/by_composite_key/{session_number}/{session_date}/{teacher_in_plan}',
                        "update": f'{api_base_url}/sessions/update',
                        "delete": f'{api_base_url}/sessions/delete/{session_number}/{session_date}/{teacher_in_plan}',
                        "sessions": f'{api_base_url}/sessions',
                        "plan": f'{api_base_url}/teachers_in_plans/search/by_id/{session_obj.teacher_in_plan}',
                        "type": f'{api_base_url}/session-types/search/by_name/{session_obj.session_type}',
                        "cabinet": f'{api_base_url}/cabinets/search/by_building_and_number/{session_obj.building_number}/{session_obj.cabinet_number}' if session_obj.cabinet_number and session_obj.building_number else None
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowSessionWithHATEOAS(session=session_pydantic, links=hateoas_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение занятия {session_number} на {session_date} для плана {teacher_in_plan} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_sessions_by_plan(self, teacher_in_plan_id: int, page: int, limit: int, request: Request, db) -> ShowSessionListWithHATEOAS:
        async with db as session:
            async with session.begin():
                teacher_in_plan_dal = TeacherInPlanDAL(session)
                session_dal = SessionDAL(session)
                try:
                    if not await ensure_teacher_in_plan_exists(teacher_in_plan_dal, teacher_in_plan_id):
                        raise HTTPException(status_code=404, detail=f"Запись в расписании преподавателя с id {teacher_in_plan_id} не найдена")

                    sessions = await session_dal.get_sessions_by_plan(teacher_in_plan_id, page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    sessions_with_hateoas = []
                    for session_obj in sessions:
                        session_dict = {
                            "session_number": session_obj.session_number,
                            "session_date": session_obj.date,
                            "teacher_in_plan": session_obj.teacher_in_plan,
                            "session_type": session_obj.session_type,
                            "cabinet_number": session_obj.cabinet_number,
                            "building_number": session_obj.building_number,
                        }
                        session_pydantic = ShowSession.model_validate(session_dict)
                        session_number = session_obj.session_number
                        session_date = session_obj.date
                        plan_id = session_obj.teacher_in_plan
                        session_links = {
                            "self": f'{api_base_url}/sessions/search/by_composite_key/{session_number}/{session_date}/{plan_id}',
                            "update": f'{api_base_url}/sessions/update',
                            "delete": f'{api_base_url}/sessions/delete/{session_number}/{session_date}/{plan_id}',
                            "sessions": f'{api_base_url}/sessions',
                            "plan": f'{api_base_url}/teachers_in_plans/search/by_id/{plan_id}',
                            "type": f'{api_base_url}/session-types/search/by_name/{session_obj.session_type}',
                            "cabinet": f'{api_base_url}/cabinets/search/by_building_and_number/{session_obj.building_number}/{session_obj.cabinet_number}' if session_obj.cabinet_number and session_obj.building_number else None
                        }
                        session_links = {k: v for k, v in session_links.items() if v is not None}
                        session_with_links = ShowSessionWithHATEOAS(session=session_pydantic, links=session_links)
                        sessions_with_hateoas.append(session_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/sessions/search/by_plan/{teacher_in_plan_id}?page={page}&limit={limit}',
                        "create": f'{api_base_url}/sessions/create',
                        "plan": f'{api_base_url}/teachers_in_plans/search/by_id/{teacher_in_plan_id}'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowSessionListWithHATEOAS(sessions=sessions_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение занятий для плана {teacher_in_plan_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_sessions_by_date(self, session_date: date, page: int, limit: int, request: Request, db) -> ShowSessionListWithHATEOAS:
        async with db as session:
            async with session.begin():
                session_dal = SessionDAL(session)
                try:
                    sessions = await session_dal.get_sessions_by_date(session_date, page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    sessions_with_hateoas = []
                    for session_obj in sessions:
                        session_dict = {
                            "session_number": session_obj.session_number,
                            "session_date": session_obj.date,
                            "teacher_in_plan": session_obj.teacher_in_plan,
                            "session_type": session_obj.session_type,
                            "cabinet_number": session_obj.cabinet_number,
                            "building_number": session_obj.building_number,
                        }
                        session_pydantic = ShowSession.model_validate(session_dict)
                        session_number = session_obj.session_number
                        plan_id = session_obj.teacher_in_plan
                        session_links = {
                            "self": f'{api_base_url}/sessions/search/by_composite_key/{session_number}/{session_date}/{plan_id}',
                            "update": f'{api_base_url}/sessions/update',
                            "delete": f'{api_base_url}/sessions/delete/{session_number}/{session_date}/{plan_id}',
                            "sessions": f'{api_base_url}/sessions',
                            "plan": f'{api_base_url}/teachers_in_plans/search/by_id/{plan_id}',
                            "type": f'{api_base_url}/session-types/search/by_name/{session_obj.session_type}',
                            "cabinet": f'{api_base_url}/cabinets/search/by_building_and_number/{session_obj.building_number}/{session_obj.cabinet_number}' if session_obj.cabinet_number and session_obj.building_number else None
                        }
                        session_links = {k: v for k, v in session_links.items() if v is not None}
                        session_with_links = ShowSessionWithHATEOAS(session=session_pydantic, links=session_links)
                        sessions_with_hateoas.append(session_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/sessions/search/by_date/{session_date}?page={page}&limit={limit}',
                        "create": f'{api_base_url}/sessions/create'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowSessionListWithHATEOAS(sessions=sessions_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение занятий на дату {session_date} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_sessions_by_type(self, session_type: str, page: int, limit: int, request: Request, db) -> ShowSessionListWithHATEOAS:
        async with db as session:
            async with session.begin():
                session_type_dal = SessionTypeDAL(session)
                session_dal = SessionDAL(session)
                try:
                    if not await ensure_session_type_exists(session_type_dal, session_type):
                        raise HTTPException(status_code=404, detail=f"Тип занятия {session_type} не найден")

                    sessions = await session_dal.get_sessions_by_type(session_type, page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    sessions_with_hateoas = []
                    for session_obj in sessions:
                        session_dict = {
                            "session_number": session_obj.session_number,
                            "session_date": session_obj.date,
                            "teacher_in_plan": session_obj.teacher_in_plan,
                            "session_type": session_obj.session_type,
                            "cabinet_number": session_obj.cabinet_number,
                            "building_number": session_obj.building_number,
                        }
                        session_pydantic = ShowSession.model_validate(session_dict)
                        session_number = session_obj.session_number
                        session_date = session_obj.date
                        plan_id = session_obj.teacher_in_plan
                        session_links = {
                            "self": f'{api_base_url}/sessions/search/by_composite_key/{session_number}/{session_date}/{plan_id}',
                            "update": f'{api_base_url}/sessions/update',
                            "delete": f'{api_base_url}/sessions/delete/{session_number}/{session_date}/{plan_id}',
                            "sessions": f'{api_base_url}/sessions',
                            "plan": f'{api_base_url}/teachers_in_plans/search/by_id/{plan_id}',
                            "type": f'{api_base_url}/session-types/search/by_name/{session_type}',
                            "cabinet": f'{api_base_url}/cabinets/search/by_building_and_number/{session_obj.building_number}/{session_obj.cabinet_number}' if session_obj.cabinet_number and session_obj.building_number else None
                        }
                        session_links = {k: v for k, v in session_links.items() if v is not None}
                        session_with_links = ShowSessionWithHATEOAS(session=session_pydantic, links=session_links)
                        sessions_with_hateoas.append(session_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/sessions/search/by_type/{session_type}?page={page}&limit={limit}',
                        "create": f'{api_base_url}/sessions/create',
                        "type": f'{api_base_url}/session-types/search/by_name/{session_type}'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowSessionListWithHATEOAS(sessions=sessions_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение занятий по типу {session_type} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_sessions_by_cabinet(self, cabinet_number: int, building_number: int, page: int, limit: int, request: Request, db) -> ShowSessionListWithHATEOAS:
        async with db as session:
            async with session.begin():
                cabinet_dal = CabinetDAL(session)
                session_dal = SessionDAL(session)
                try:
                    if not await ensure_cabinet_exists(cabinet_dal, building_number, cabinet_number):
                        raise HTTPException(status_code=404, detail=f"Кабинет {cabinet_number} в здании {building_number} не найден")

                    sessions = await session_dal.get_sessions_by_cabinet(cabinet_number, building_number, page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    sessions_with_hateoas = []
                    for session_obj in sessions:
                        session_dict = {
                            "session_number": session_obj.session_number,
                            "session_date": session_obj.date,
                            "teacher_in_plan": session_obj.teacher_in_plan,
                            "session_type": session_obj.session_type,
                            "cabinet_number": session_obj.cabinet_number,
                            "building_number": session_obj.building_number,
                        }
                        session_pydantic = ShowSession.model_validate(session_dict)
                        session_number = session_obj.session_number
                        session_date = session_obj.date
                        plan_id = session_obj.teacher_in_plan
                        session_links = {
                            "self": f'{api_base_url}/sessions/search/by_composite_key/{session_number}/{session_date}/{plan_id}',
                            "update": f'{api_base_url}/sessions/update',
                            "delete": f'{api_base_url}/sessions/delete/{session_number}/{session_date}/{plan_id}',
                            "sessions": f'{api_base_url}/sessions',
                            "plan": f'{api_base_url}/teachers_in_plans/search/by_id/{plan_id}',
                            "type": f'{api_base_url}/session-types/search/by_name/{session_obj.session_type}',
                            "cabinet": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}'
                        }
                        session_with_links = ShowSessionWithHATEOAS(session=session_pydantic, links=session_links)
                        sessions_with_hateoas.append(session_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/sessions/search/by_cabinet/{building_number}/{cabinet_number}?page={page}&limit={limit}',
                        "create": f'{api_base_url}/sessions/create',
                        "cabinet": f'{api_base_url}/cabinets/search/by_building_and_number/{building_number}/{cabinet_number}'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowSessionListWithHATEOAS(sessions=sessions_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение занятий для кабинета {cabinet_number} в здании {building_number} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_all_sessions(self, page: int, limit: int, request: Request, db) -> ShowSessionListWithHATEOAS:
        async with db as session:
            async with session.begin():
                session_dal = SessionDAL(session)
                try:
                    sessions = await session_dal.get_all_sessions(page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    sessions_with_hateoas = []
                    for session_obj in sessions:
                        session_dict = {
                            "session_number": session_obj.session_number,
                            "session_date": session_obj.date,
                            "teacher_in_plan": session_obj.teacher_in_plan,
                            "session_type": session_obj.session_type,
                            "cabinet_number": session_obj.cabinet_number,
                            "building_number": session_obj.building_number,
                        }
                        session_pydantic = ShowSession.model_validate(session_dict)
                        session_number = session_obj.session_number
                        session_date = session_obj.date
                        plan_id = session_obj.teacher_in_plan
                        session_links = {
                            "self": f'{api_base_url}/sessions/search/by_composite_key/{session_number}/{session_date}/{plan_id}',
                            "update": f'{api_base_url}/sessions/update',
                            "delete": f'{api_base_url}/sessions/delete/{session_number}/{session_date}/{plan_id}',
                            "sessions": f'{api_base_url}/sessions',
                            "plan": f'{api_base_url}/teachers_in_plans/search/by_id/{plan_id}',
                            "type": f'{api_base_url}/session-types/search/by_name/{session_obj.session_type}',
                            "cabinet": f'{api_base_url}/cabinets/search/by_building_and_number/{session_obj.building_number}/{session_obj.cabinet_number}' if session_obj.cabinet_number and session_obj.building_number else None
                        }
                        session_links = {k: v for k, v in session_links.items() if v is not None}
                        session_with_links = ShowSessionWithHATEOAS(session=session_pydantic, links=session_links)
                        sessions_with_hateoas.append(session_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/sessions/search?page={page}&limit={limit}',
                        "create": f'{api_base_url}/sessions/create'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowSessionListWithHATEOAS(sessions=sessions_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение занятий отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _delete_session(self, session_number: int, session_date: date, teacher_in_plan: int, request: Request, db) -> ShowSessionWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    session_dal = SessionDAL(session)
                    session_obj = await session_dal.get_session_by_composite_key(session_number, session_date, teacher_in_plan)
                    if not session_obj:
                        raise HTTPException(status_code=404, detail=f"Занятие с номером {session_number}, датой {session_date} и записью в расписании преподавателя {teacher_in_plan} не найдено")

                    deleted_session_obj = await session_dal.delete_session(session_number, session_date, teacher_in_plan)
                    
                    if not deleted_session_obj:
                        raise HTTPException(status_code=404, detail=f"Занятие с номером {session_number}, датой {session_date} и записью в расписании преподавателя {teacher_in_plan} не найдено")

                    session_dict = {
                        "session_number": deleted_session_obj.session_number,
                        "session_date": deleted_session_obj.date,
                        "teacher_in_plan": deleted_session_obj.teacher_in_plan,
                        "session_type": deleted_session_obj.session_type,
                        "cabinet_number": deleted_session_obj.cabinet_number,
                        "building_number": deleted_session_obj.building_number,
                    }
                    session_pydantic = ShowSession.model_validate(session_dict)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "sessions": f'{api_base_url}/sessions',
                        "create": f'{api_base_url}/sessions/create'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowSessionWithHATEOAS(session=session_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при удалении занятия {session_number} на {session_date} для плана {teacher_in_plan}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении занятия.")


    async def _update_session(self, body: UpdateSession, request: Request, db) -> ShowSessionWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["session_number", "session_date", "teacher_in_plan", "new_session_number", "new_session_date", "new_teacher_in_plan", "new_cabinet_number", "new_building_number"]}

                    target_session_number = body.session_number
                    target_session_date = body.session_date
                    target_teacher_in_plan = body.teacher_in_plan
                    if body.new_session_number is not None:
                        update_data["session_number"] = body.new_session_number
                        target_session_number = body.new_session_number
                    if body.new_session_date is not None:
                        update_data["date"] = body.new_session_date 
                        target_session_date = body.new_session_date
                    if body.new_teacher_in_plan is not None:
                        update_data["teacher_in_plan"] = body.new_teacher_in_plan
                        target_teacher_in_plan = body.new_teacher_in_plan
                        
                    if body.new_cabinet_number is not None:
                        update_data["cabinet_number"] = body.new_cabinet_number
                    if body.new_building_number is not None:
                        update_data["building_number"] = body.new_building_number

                    if "session_type" in update_data:
                        session_type_dal = SessionTypeDAL(session)
                        if not await ensure_session_type_exists(session_type_dal, update_data["session_type"]):
                            raise HTTPException(status_code=404, detail=f"Тип занятия {update_data['session_type']} не найден")
                        
                    if "cabinet_number" in update_data or "building_number" in update_data:
                        cabinet_number_to_check = update_data.get("cabinet_number")
                        building_number_to_check = update_data.get("building_number")
                        
                        if cabinet_number_to_check is not None and building_number_to_check is not None:
                            cabinet_dal = CabinetDAL(session)
                            
                            cabinet_exists = await cabinet_dal.get_cabinet_by_number_and_building(building_number_to_check, cabinet_number_to_check)
                            if not cabinet_exists:
                                raise HTTPException(status_code=404, detail=f"Кабинет {cabinet_number_to_check} в здании {building_number_to_check} не найден")

                    session_dal = SessionDAL(session)

                    session_obj = await session_dal.get_session_by_composite_key(body.session_number, body.session_date, body.teacher_in_plan)
                    if not session_obj:
                        raise HTTPException(status_code=404, detail=f"Занятие с номером {body.session_number}, датой {body.session_date} и записью в расписании преподавателя {body.teacher_in_plan} не найдено")

                    if (target_session_number, target_session_date, target_teacher_in_plan) != (body.session_number, body.session_date, body.teacher_in_plan):
                        existing_new_session = await session_dal.get_session_by_composite_key(target_session_number, target_session_date, target_teacher_in_plan)
                        if existing_new_session:
                            raise HTTPException(status_code=400, detail=f"Занятие с номером {target_session_number}, датой {target_session_date} и записью в расписании преподавателя {target_teacher_in_plan} уже существует")

                    updated_session_obj = await session_dal.update_session(target_session_number=body.session_number, target_session_date=body.session_date, target_teacher_in_plan=body.teacher_in_plan, **update_data)
                    if not updated_session_obj:
                        raise HTTPException(status_code=404, detail=f"Занятие с номером {body.session_number}, датой {body.session_date} и записью в расписании преподавателя {body.teacher_in_plan} не найдено")

                    session_number = updated_session_obj.session_number
                    session_date = updated_session_obj.date
                    teacher_in_plan_id = updated_session_obj.teacher_in_plan
                    
                    session_dict = {
                        "session_number": updated_session_obj.session_number,
                        "session_date": updated_session_obj.date,
                        "teacher_in_plan": updated_session_obj.teacher_in_plan,
                        "session_type": updated_session_obj.session_type,
                        "cabinet_number": updated_session_obj.cabinet_number,
                        "building_number": updated_session_obj.building_number,
                    }
                    session_pydantic = ShowSession.model_validate(session_dict)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/sessions/search/by_composite_key/{session_number}/{session_date}/{teacher_in_plan_id}',
                        "update": f'{api_base_url}/sessions/update',
                        "delete": f'{api_base_url}/sessions/delete/{session_number}/{session_date}/{teacher_in_plan_id}',
                        "sessions": f'{api_base_url}/sessions',
                        "plan": f'{api_base_url}/teachers_in_plans/search/by_id/{updated_session_obj.teacher_in_plan}',
                        "type": f'{api_base_url}/session-types/search/by_name/{updated_session_obj.session_type}',
                        "cabinet": f'{api_base_url}/cabinets/search/by_building_and_number/{updated_session_obj.building_number}/{updated_session_obj.cabinet_number}' if updated_session_obj.cabinet_number and updated_session_obj.building_number else None
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowSessionWithHATEOAS(session=session_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.warning(f"Изменение данных о занятии отменено (Ошибка: {e})")
                raise e
