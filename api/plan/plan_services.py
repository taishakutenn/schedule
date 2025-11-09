from api.plan.plan_pydantic import *
from api.services_helpers import ensure_plan_exists, ensure_speciality_exists
from api.plan.plan_DAL import PlanDAL 
from api.speciality.speciality_DAL import SpecialityDAL
from fastapi import HTTPException, Request

from config.logging_config import configure_logging

# Create logger object
logger = configure_logging()


class PlanService:
    async def _create_new_plan(self, body: CreatePlan, request: Request, db) -> ShowPlanWithHATEOAS:
        async with db as session:
            async with session.begin():
                speciality_dal = SpecialityDAL(session)
                plan_dal = PlanDAL(session)
                try:
                    if not await ensure_speciality_exists(speciality_dal, body.speciality_code):
                        raise HTTPException(status_code=404, detail=f"Специальность с кодом {body.speciality_code} не найдена")

                    plan = await plan_dal.create_plan(
                        year=body.year,
                        speciality_code=body.speciality_code
                    )
                    plan_id = plan.id 
                    plan_pydantic = ShowPlan.model_validate(plan, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/plans/search/by_id/{plan_id}',
                        "update": f'{api_base_url}/plans/update',
                        "delete": f'{api_base_url}/plans/delete/{plan_id}',
                        "plans": f'{api_base_url}/plans',
                        "speciality": f'{api_base_url}/specialities/search/by_speciality_code/{body.speciality_code}',
                        "chapters": f'{api_base_url}/chapters/search/by_plan/{plan_id}',
                        "semesters": f'{api_base_url}/semesters/search/by_plan/{plan_id}'
                    }

                    return ShowPlanWithHATEOAS(plan=plan_pydantic, links=hateoas_links)

                except HTTPException:
                    await session.rollback()
                    raise
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Неожиданная ошибка при создании учебного плана для специальности {body.speciality_code} на {body.year} год: {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_plan_by_id(self, plan_id: int, request: Request, db) -> ShowPlanWithHATEOAS:
        async with db as session:
            async with session.begin():
                plan_dal = PlanDAL(session)
                try:
                    plan = await plan_dal.get_plan_by_id(plan_id)
                    if not plan:
                        raise HTTPException(status_code=404, detail=f"Учебный план с id {plan_id} не найден")
                    plan_pydantic = ShowPlan.model_validate(plan, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/plans/search/by_id/{plan_id}',
                        "update": f'{api_base_url}/plans/update',
                        "delete": f'{api_base_url}/plans/delete/{plan_id}',
                        "plans": f'{api_base_url}/plans',
                        "speciality": f'{api_base_url}/specialities/search/by_speciality_code/{plan.speciality_code}',
                        "chapters": f'{api_base_url}/chapters/search/by_plan/{plan_id}',
                        "semesters": f'{api_base_url}/semesters/search/by_plan/{plan_id}'
                    }

                    return ShowPlanWithHATEOAS(plan=plan_pydantic, links=hateoas_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение учебного плана {plan_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_all_plans(self, page: int, limit: int, request: Request, db) -> ShowPlanListWithHATEOAS:
        async with db as session:
            async with session.begin():
                plan_dal = PlanDAL(session)
                try:
                    plans = await plan_dal.get_all_plans(page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    plans_with_hateoas = []
                    for plan in plans:
                        plan_pydantic = ShowPlan.model_validate(plan, from_attributes=True)
                        plan_id = plan.id
                        plan_links = {
                            "self": f'{api_base_url}/plans/search/by_id/{plan_id}',
                            "update": f'{api_base_url}/plans/update',
                            "delete": f'{api_base_url}/plans/delete/{plan_id}',
                            "plans": f'{api_base_url}/plans',
                            "speciality": f'{api_base_url}/specialities/search/by_speciality_code/{plan.speciality_code}',
                            "chapters": f'{api_base_url}/chapters/search/by_plan/{plan_id}',
                            "semesters": f'{api_base_url}/semesters/search/by_plan/{plan_id}'
                        }
                        plan_with_links = ShowPlanWithHATEOAS(plan=plan_pydantic, links=plan_links)
                        plans_with_hateoas.append(plan_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/plans/search?page={page}&limit={limit}',
                        "create": f'{api_base_url}/plans/create'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowPlanListWithHATEOAS(plans=plans_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение учебных планов отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _delete_plan(self, plan_id: int, request: Request, db) -> ShowPlanWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    plan_dal = PlanDAL(session)
                    
                    if not await ensure_plan_exists(plan_dal, plan_id):
                        raise HTTPException(status_code=404, detail=f"Учебный план с id {plan_id} не найден")

                    plan = await plan_dal.delete_plan(plan_id)

                    if not plan:
                        raise HTTPException(status_code=404, detail=f"Учебный план с id {plan_id} не найден")

                    plan_pydantic = ShowPlan.model_validate(plan, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "plans": f'{api_base_url}/plans',
                        "create": f'{api_base_url}/plans/create'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowPlanWithHATEOAS(plan=plan_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при удалении учебного плана {plan_id}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении учебного плана.")


    async def _update_plan(self, body: UpdatePlan, request: Request, db) -> ShowPlanWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    
                    update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["plan_id"]}
                    
                    if "speciality_code" in update_data:
                        speciality_code_to_check = update_data["speciality_code"]
                        speciality_dal = SpecialityDAL(session)
                        if not await ensure_speciality_exists(speciality_dal, speciality_code_to_check):
                            raise HTTPException(status_code=404, detail=f"Специальность с кодом {speciality_code_to_check} не найдена")

                    plan_dal = PlanDAL(session)

                    if not await ensure_plan_exists(plan_dal, body.plan_id):
                        raise HTTPException(status_code=404, detail=f"Учебный план с id {body.plan_id} не найден")

                    plan = await plan_dal.update_plan(target_id=body.plan_id, **update_data)
                    if not plan:
                        raise HTTPException(status_code=404, detail=f"Учебный план с id {body.plan_id} не найден")

                    plan_id = plan.id 
                    plan_pydantic = ShowPlan.model_validate(plan, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/plans/search/by_id/{plan_id}',
                        "update": f'{api_base_url}/plans/update',
                        "delete": f'{api_base_url}/plans/delete/{plan_id}',
                        "plans": f'{api_base_url}/plans',
                        "speciality": f'{api_base_url}/specialities/search/by_speciality_code/{plan.speciality_code}',
                        "chapters": f'{api_base_url}/chapters/search/by_plan/{plan_id}',
                        "semesters": f'{api_base_url}/semesters/search/by_plan/{plan_id}'
                    }

                    return ShowPlanWithHATEOAS(plan=plan_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.warning(f"Изменение данных о учебном плане отменено (Ошибка: {e})")
                raise e
            