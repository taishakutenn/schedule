from api.semester.semester_pydantic import *
from api.services_helpers import ensure_plan_exists, ensure_semester_exists, ensure_semester_unique
from api.semester.semester_DAL import SemesterDAL 
from api.plan.plan_DAL import PlanDAL
from fastapi import HTTPException, Request

from config.logging_config import configure_logging

# Create logger object
logger = configure_logging()


class SemesterService:
    async def _create_new_semester(self, body: CreateSemester, request: Request, db) -> ShowSemesterWithHATEOAS:
        async with db as session:
            async with session.begin():
                plan_dal = PlanDAL(session)
                semester_dal = SemesterDAL(session)
                try:
                    if not await ensure_plan_exists(plan_dal, body.plan_id):
                        raise HTTPException(status_code=404, detail=f"Учебный план с id {body.plan_id} не найден")
                    if not await ensure_semester_unique(semester_dal, body.semester, body.plan_id):
                        raise HTTPException(status_code=400, detail=f"Семестр {body.semester} для плана {body.plan_id} уже существует")

                    semester_obj = await semester_dal.create_semester(
                        semester=body.semester,
                        weeks=body.weeks,
                        practice_weeks=body.practice_weeks,
                        plan_id=body.plan_id
                    )
                    semester_number = semester_obj.semester
                    plan_id = semester_obj.plan_id
                    semester_pydantic = ShowSemester.model_validate(semester_obj, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/semesters/search/by_semester_and_plan/{semester_number}/{plan_id}',
                        "update": f'{api_base_url}/semesters/update',
                        "delete": f'{api_base_url}/semesters/delete/{semester_number}/{plan_id}',
                        "semesters": f'{api_base_url}/semesters',
                        "plan": f'{api_base_url}/plans/search/by_id/{plan_id}'
                    }

                    return ShowSemesterWithHATEOAS(semester=semester_pydantic, links=hateoas_links)

                except HTTPException:
                    await session.rollback()
                    raise
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Неожиданная ошибка при создании семестра {body.semester} для плана {body.plan_id}: {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_semester_by_semester_and_plan(self, semester: int, plan_id: int, request: Request, db) -> ShowSemesterWithHATEOAS:
        async with db as session:
            async with session.begin():
                semester_dal = SemesterDAL(session)
                try:
                    semester_obj = await semester_dal.get_semester_by_semester_and_plan(semester, plan_id)
                    if not semester_obj:
                        raise HTTPException(status_code=404, detail=f"Семестр {semester} для плана {plan_id} не найден")
                    semester_pydantic = ShowSemester.model_validate(semester_obj, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/semesters/search/by_semester_and_plan/{semester}/{plan_id}',
                        "update": f'{api_base_url}/semesters/update',
                        "delete": f'{api_base_url}/semesters/delete/{semester}/{plan_id}',
                        "semesters": f'{api_base_url}/semesters',
                        "plan": f'{api_base_url}/plans/search/by_id/{plan_id}'
                    }

                    return ShowSemesterWithHATEOAS(semester=semester_pydantic, links=hateoas_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение семестра {semester} для плана {plan_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_all_semesters(self, page: int, limit: int, request: Request, db) -> ShowSemesterListWithHATEOAS:
        async with db as session:
            async with session.begin():
                semester_dal = SemesterDAL(session)
                try:
                    semesters = await semester_dal.get_all_semesters(page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    semesters_with_hateoas = []
                    for semester_obj in semesters:
                        semester_pydantic = ShowSemester.model_validate(semester_obj, from_attributes=True)
                        semester_number = semester_obj.semester
                        plan_id = semester_obj.plan_id
                        semester_links = {
                            "self": f'{api_base_url}/semesters/search/by_semester_and_plan/{semester_number}/{plan_id}',
                            "update": f'{api_base_url}/semesters/update',
                            "delete": f'{api_base_url}/semesters/delete/{semester_number}/{plan_id}',
                            "semesters": f'{api_base_url}/semesters',
                            "plan": f'{api_base_url}/plans/search/by_id/{plan_id}'
                        }
                        semester_with_links = ShowSemesterWithHATEOAS(semester=semester_pydantic, links=semester_links)
                        semesters_with_hateoas.append(semester_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/semesters/search?page={page}&limit={limit}',
                        "create": f'{api_base_url}/semesters/create'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowSemesterListWithHATEOAS(semesters=semesters_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение семестров отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _delete_semester(self, semester: int, plan_id: int, request: Request, db) -> ShowSemesterWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    semester_dal = SemesterDAL(session)
                    if not await ensure_semester_exists(semester_dal, semester, plan_id):
                        raise HTTPException(status_code=404, detail=f"Семестр {semester} для плана {plan_id} не найден")

                    semester_obj = await semester_dal.delete_semester(semester, plan_id)
                    if not semester_obj:
                        raise HTTPException(status_code=404, detail=f"Семестр {semester} для плана {plan_id} не найден")

                    semester_pydantic = ShowSemester.model_validate(semester_obj, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "semesters": f'{api_base_url}/semesters',
                        "create": f'{api_base_url}/semesters/create',
                        "plan": f'{api_base_url}/plans/search/by_id/{plan_id}'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowSemesterWithHATEOAS(semester=semester_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при удалении семестра {semester} в плане {plan_id}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении семестра.")


    async def _update_semester(self, body: UpdateSemester, request: Request, db) -> ShowSemesterWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["semester", "plan_id", "new_semester", "new_plan_id"]}
                    target_semester = body.semester
                    target_plan_id = body.plan_id
                    if body.new_semester is not None or body.new_plan_id is not None:
                        if body.new_semester is not None:
                            update_data["semester"] = body.new_semester
                            target_semester = body.new_semester 
                        if body.new_plan_id is not None:
                            update_data["plan_id"] = body.new_plan_id
                            target_plan_id = body.new_plan_id 
                            
                        if (target_semester, target_plan_id) != (body.semester, body.plan_id):
                            semester_dal = SemesterDAL(session)
                            if not await ensure_semester_unique(semester_dal, target_semester, target_plan_id):
                                raise HTTPException(status_code=400, detail=f"Семестр {target_semester} для плана {target_plan_id} уже существует")

                    semester_dal = SemesterDAL(session)

                    if not await ensure_semester_exists(semester_dal, body.semester, body.plan_id):
                        raise HTTPException(status_code=404, detail=f"Семестр {body.semester} для плана {body.plan_id} не найден")

                    if "plan_id" in update_data:
                        plan_id_to_check = update_data["plan_id"]
                        plan_dal = PlanDAL(session)
                        if not await ensure_plan_exists(plan_dal, plan_id_to_check):
                            raise HTTPException(status_code=404, detail=f"Учебный план с id {plan_id_to_check} не найден")

                    semester_obj = await semester_dal.update_semester(target_semester=body.semester, target_plan_id=body.plan_id, **update_data)
                    if not semester_obj:
                        raise HTTPException(status_code=404, detail=f"Семестр {body.semester} для плана {body.plan_id} не найден")

                    semester_number = semester_obj.semester 
                    plan_id = semester_obj.plan_id
                    semester_pydantic = ShowSemester.model_validate(semester_obj, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/semesters/search/by_semester_and_plan/{semester_number}/{plan_id}',
                        "update": f'{api_base_url}/semesters/update',
                        "delete": f'{api_base_url}/semesters/delete/{semester_number}/{plan_id}',
                        "semesters": f'{api_base_url}/semesters',
                        "plan": f'{api_base_url}/plans/search/by_id/{plan_id}'
                    }

                    return ShowSemesterWithHATEOAS(semester=semester_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.warning(f"Изменение данных о семестре отменено (Ошибка: {e})")
                raise e
