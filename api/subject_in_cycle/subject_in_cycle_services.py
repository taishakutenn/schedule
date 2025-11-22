from api.subject_in_cycle.subject_in_cycle_pydantic import *
from api.services_helpers import ensure_cycle_exists, ensure_module_exists, ensure_subject_in_cycle_exists
from api.subject_in_cycle.subject_in_cycle_DAL import SubjectsInCycleDAL
from api.module.module_DAL import ModuleDAL
from api.cycle.cycle_DAL import CycleDAL
from api.group.group_DAL import GroupDAL
from api.plan.plan_DAL import PlanDAL
from api.chapter.chapter_DAL import ChapterDAL
from api.semester.semester_DAL import SemesterDAL
from api.teacher_in_plan.teacher_in_plan_DAL import TeacherInPlanDAL
from fastapi import HTTPException, Request

from api.subject_in_cycle_hours.subject_in_cycle_hours_DAL import SubjectsInCycleHoursDAL
from api.subject_in_cycle_hours.subject_in_cycle_hours_pydantic import ShowSubjectsInCycleHours
from config.logging_config import configure_logging

# Create logger object
logger = configure_logging()


class SubjectInCycleService:
    async def _create_new_subject_in_cycle(self, body: CreateSubjectsInCycle, request: Request, db) -> ShowSubjectsInCycleWithHATEOAS:
        async with db as session:
            async with session.begin():
                cycle_dal = CycleDAL(session)
                module_dal = ModuleDAL(session)
                subject_in_cycle_dal = SubjectsInCycleDAL(session)
                try:
                    if body.cycle_in_chapter_id is not None:
                        if not await ensure_cycle_exists(cycle_dal, body.cycle_in_chapter_id):
                            raise HTTPException(status_code=404, detail=f"Цикл с id {body.cycle_in_chapter_id} не найден")

                    if body.module_in_cycle_id is not None:
                        if not await ensure_module_exists(module_dal, body.module_in_cycle_id):
                            raise HTTPException(status_code=404, detail=f"Модуль с id {body.module_in_cycle_id} не найден")
                        if body.cycle_in_chapter_id is not None:
                            module_obj = await module_dal.get_module_by_id(body.module_in_cycle_id)
                            if module_obj.cycle_in_chapter_id != body.cycle_in_chapter_id:
                                raise HTTPException(status_code=400, detail=f"Модуль с id {body.module_in_cycle_id} не принадлежит циклу с id {body.cycle_in_chapter_id}")
                    
                    subject_in_cycle = await subject_in_cycle_dal.create_subject_in_cycle(
                        code=body.code,
                        title=body.title,
                        cycle_in_chapter_id=body.cycle_in_chapter_id,
                        module_in_cycle_id=body.module_in_cycle_id
                    )
                    subject_in_cycle_id = subject_in_cycle.id 
                    subject_in_cycle_pydantic = ShowSubjectsInCycle.model_validate(subject_in_cycle, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_in_cycle_id}',
                        "update": f'{api_base_url}/subjects_in_cycles/update',
                        "delete": f'{api_base_url}/subjects_in_cycles/delete/{subject_in_cycle_id}',
                        "subjects_in_cycles": f'{api_base_url}/subjects_in_cycles',
                        "cycle": f'{api_base_url}/cycles/search/by_id/{body.cycle_in_chapter_id}',
                        "module": f'{api_base_url}/modules/search/by_id/{body.module_in_cycle_id}' if body.module_in_cycle_id else None,
                        "hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_subject_in_cycle/{subject_in_cycle_id}',
                        "streams": f'{api_base_url}/streams/search/by_subject_in_cycle/{subject_in_cycle_id}'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowSubjectsInCycleWithHATEOAS(subject_in_cycle=subject_in_cycle_pydantic, links=hateoas_links)

                except HTTPException:
                    await session.rollback()
                    raise
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Неожиданная ошибка при создании предмета '{body.title}' в цикле {body.cycle_in_chapter_id}: {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_subject_in_cycle_by_id(self, subject_in_cycle_id: int, request: Request, db) -> ShowSubjectsInCycleWithHATEOAS:
        async with db as session:
            async with session.begin():
                subject_in_cycle_dal = SubjectsInCycleDAL(session)
                try:
                    subject_in_cycle = await subject_in_cycle_dal.get_subject_in_cycle_by_id(subject_in_cycle_id)
                    if not subject_in_cycle:
                        raise HTTPException(status_code=404, detail=f"Предмет в цикле с id {subject_in_cycle_id} не найден")
                    subject_in_cycle_pydantic = ShowSubjectsInCycle.model_validate(subject_in_cycle, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_in_cycle_id}',
                        "update": f'{api_base_url}/subjects_in_cycles/update',
                        "delete": f'{api_base_url}/subjects_in_cycles/delete/{subject_in_cycle_id}',
                        "subjects_in_cycles": f'{api_base_url}/subjects_in_cycles',
                        "cycle": f'{api_base_url}/cycles/search/by_id/{subject_in_cycle.cycle_in_chapter_id}',
                        "module": f'{api_base_url}/modules/search/by_id/{subject_in_cycle.module_in_cycle_id}' if subject_in_cycle.module_in_cycle_id else None,
                        "hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_subject_in_cycle/{subject_in_cycle_id}',
                        "streams": f'{api_base_url}/streams/search/by_subject_in_cycle/{subject_in_cycle_id}'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowSubjectsInCycleWithHATEOAS(subject_in_cycle=subject_in_cycle_pydantic, links=hateoas_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение предмета в цикле {subject_in_cycle_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_subjects_in_cycle_by_cycle(self, cycle_in_chapter_id: int, page: int, limit: int, request: Request, db) -> ShowSubjectsInCycleListWithHATEOAS:
        async with db as session:
            async with session.begin():
                cycle_dal = CycleDAL(session)
                subject_in_cycle_dal = SubjectsInCycleDAL(session)
                try:
                    if not await ensure_cycle_exists(cycle_dal, cycle_in_chapter_id):
                        raise HTTPException(status_code=404, detail=f"Цикл с id {cycle_in_chapter_id} не найден")

                    subjects_in_cycles = await subject_in_cycle_dal.get_subjects_in_cycle_by_cycle(cycle_in_chapter_id, page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    subjects_in_cycles_with_hateoas = []
                    for subject_in_cycle in subjects_in_cycles:
                        subject_in_cycle_pydantic = ShowSubjectsInCycle.model_validate(subject_in_cycle, from_attributes=True)
                        subject_in_cycle_id = subject_in_cycle.id
                        subject_in_cycle_links = {
                            "self": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_in_cycle_id}',
                            "update": f'{api_base_url}/subjects_in_cycles/update',
                            "delete": f'{api_base_url}/subjects_in_cycles/delete/{subject_in_cycle_id}',
                            "subjects_in_cycles": f'{api_base_url}/subjects_in_cycles',
                            "cycle": f'{api_base_url}/cycles/search/by_id/{cycle_in_chapter_id}',
                            "module": f'{api_base_url}/modules/search/by_id/{subject_in_cycle.module_in_cycle_id}' if subject_in_cycle.module_in_cycle_id else None,
                            "hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_subject_in_cycle/{subject_in_cycle_id}',
                            "streams": f'{api_base_url}/streams/search/by_subject_in_cycle/{subject_in_cycle_id}'
                        }
                        subject_in_cycle_links = {k: v for k, v in subject_in_cycle_links.items() if v is not None}
                        subject_in_cycle_with_links = ShowSubjectsInCycleWithHATEOAS(subject_in_cycle=subject_in_cycle_pydantic, links=subject_in_cycle_links)
                        subjects_in_cycles_with_hateoas.append(subject_in_cycle_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/subjects_in_cycles/search/by_cycle/{cycle_in_chapter_id}?page={page}&limit={limit}',
                        "create": f'{api_base_url}/subjects_in_cycles/create',
                        "cycle": f'{api_base_url}/cycles/search/by_id/{cycle_in_chapter_id}'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowSubjectsInCycleListWithHATEOAS(subjects_in_cycles=subjects_in_cycles_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение предметов в цикле для цикла {cycle_in_chapter_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_subjects_in_cycle_by_module(self, module_in_cycle_id: int, page: int, limit: int, request: Request, db) -> ShowSubjectsInCycleListWithHATEOAS:
        async with db as session:
            async with session.begin():
                module_dal = ModuleDAL(session)
                subject_in_cycle_dal = SubjectsInCycleDAL(session)
                try:
                    if not await ensure_module_exists(module_dal, module_in_cycle_id):
                        raise HTTPException(status_code=404, detail=f"Модуль с id {module_in_cycle_id} не найден")

                    subjects_in_cycles = await subject_in_cycle_dal.get_subjects_in_cycle_by_module(module_in_cycle_id, page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    subjects_in_cycles_with_hateoas = []
                    for subject_in_cycle in subjects_in_cycles:
                        subject_in_cycle_pydantic = ShowSubjectsInCycle.model_validate(subject_in_cycle, from_attributes=True)
                        subject_in_cycle_id = subject_in_cycle.id
                        subject_in_cycle_links = {
                            "self": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_in_cycle_id}',
                            "update": f'{api_base_url}/subjects_in_cycles/update',
                            "delete": f'{api_base_url}/subjects_in_cycles/delete/{subject_in_cycle_id}',
                            "subjects_in_cycles": f'{api_base_url}/subjects_in_cycles',
                            "cycle": f'{api_base_url}/cycles/search/by_id/{subject_in_cycle.cycle_in_chapter_id}',
                            "module": f'{api_base_url}/modules/search/by_id/{module_in_cycle_id}',
                            "hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_subject_in_cycle/{subject_in_cycle_id}',
                            "streams": f'{api_base_url}/streams/search/by_subject_in_cycle/{subject_in_cycle_id}'
                        }
                        subject_in_cycle_links = {k: v for k, v in subject_in_cycle_links.items() if v is not None}
                        subject_in_cycle_with_links = ShowSubjectsInCycleWithHATEOAS(subject_in_cycle=subject_in_cycle_pydantic, links=subject_in_cycle_links)
                        subjects_in_cycles_with_hateoas.append(subject_in_cycle_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/subjects_in_cycles/search/by_module/{module_in_cycle_id}?page={page}&limit={limit}',
                        "create": f'{api_base_url}/subjects_in_cycles/create',
                        "module": f'{api_base_url}/modules/search/by_id/{module_in_cycle_id}'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowSubjectsInCycleListWithHATEOAS(subjects_in_cycles=subjects_in_cycles_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение предметов в цикле для модуля {module_in_cycle_id} отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_all_subjects_in_cycles(self, page: int, limit: int, request: Request, db) -> ShowSubjectsInCycleListWithHATEOAS:
        async with db as session:
            async with session.begin():
                subject_in_cycle_dal = SubjectsInCycleDAL(session)
                try:
                    subjects_in_cycles = await subject_in_cycle_dal.get_all_subjects_in_cycles(page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    subjects_in_cycles_with_hateoas = []
                    for subject_in_cycle in subjects_in_cycles:
                        subject_in_cycle_pydantic = ShowSubjectsInCycle.model_validate(subject_in_cycle, from_attributes=True)
                        subject_in_cycle_id = subject_in_cycle.id
                        subject_in_cycle_links = {
                            "self": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_in_cycle_id}',
                            "update": f'{api_base_url}/subjects_in_cycles/update',
                            "delete": f'{api_base_url}/subjects_in_cycles/delete/{subject_in_cycle_id}',
                            "subjects_in_cycles": f'{api_base_url}/subjects_in_cycles',
                            "cycle": f'{api_base_url}/cycles/search/by_id/{subject_in_cycle.cycle_in_chapter_id}',
                            "module": f'{api_base_url}/modules/search/by_id/{subject_in_cycle.module_in_cycle_id}' if subject_in_cycle.module_in_cycle_id else None,
                            "hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_subject_in_cycle/{subject_in_cycle_id}',
                            "streams": f'{api_base_url}/streams/search/by_subject_in_cycle/{subject_in_cycle_id}'
                        }
                        subject_in_cycle_links = {k: v for k, v in subject_in_cycle_links.items() if v is not None}
                        subject_in_cycle_with_links = ShowSubjectsInCycleWithHATEOAS(subject_in_cycle=subject_in_cycle_pydantic, links=subject_in_cycle_links)
                        subjects_in_cycles_with_hateoas.append(subject_in_cycle_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/subjects_in_cycles/search?page={page}&limit={limit}',
                        "create": f'{api_base_url}/subjects_in_cycles/create'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowSubjectsInCycleListWithHATEOAS(subjects_in_cycles=subjects_in_cycles_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение предметов в цикле отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_info_to_create_schedule(self, group_name: str, semester: int, db):
        async def get_info_for_subjects(plan_id):
            subjects_with_hours = []
            # Get all chapters for this plan
            chapters = await chapter_dal.get_chapters_by_plan(plan_id, page=0, limit=100)
            for chapter in chapters:
                # Get of cycles for this chapter
                cycles = await cycle_dal.get_cycles_by_chapter(chapter.id, page=0, limit=100)
                for cycle in cycles:
                    # Get of cycles for this chapter
                    subjects_in_cycle_list = await subject_in_cycle_dal.get_subjects_in_cycle_by_cycle(cycle.id, page=0, limit=100)
                    for subject_orm in subjects_in_cycle_list:
                        # Get subjects from this cycle and create to pydantic
                        subject_pydantic = ShowSubjectsInCycle.model_validate(subject_orm, from_attributes=True)

                        # Get hours for the current subject
                        hours_list = await subject_in_cycle_hours_dal.get_subjects_in_cycle_hours_by_subject_and_semester(
                            subject_orm.id, semester
                        )

                        # If hours for subject with this id is empty
                        if not hours_list:
                            print("Нет часов для такого предмета")
                            continue

                        # Hour list to pydantic
                        hours_pydantic_list = [
                            ShowSubjectsInCycleHours.model_validate(hour_orm, from_attributes=True)
                            for hour_orm in hours_list
                        ]

                        # Get teacher for this subject and group
                        teacher = await\
                            teacher_in_plan_dal.get_teacher_in_plan_by_group_and_subject_in_cycle_hours(group_name,
                                                                                                        hours_list[0].id)

                        subject_with_hours_info = {
                            "teacher": teacher,
                            "subject": subject_pydantic,
                            "hours": hours_pydantic_list
                        }
                        subjects_with_hours.append(subject_with_hours_info)

            return subjects_with_hours

        async with db as session:
            async with session.begin():
                # Ini dals
                group_dal = GroupDAL(session)
                plan_dal = PlanDAL(session)
                chapter_dal = ChapterDAL(session)
                cycle_dal = CycleDAL(session)
                subject_in_cycle_dal = SubjectsInCycleDAL(session)
                subject_in_cycle_hours_dal = SubjectsInCycleHoursDAL(session)
                semester_dal = SemesterDAL(session)
                teacher_in_plan_dal = TeacherInPlanDAL(session)

                # Get group data
                group = await group_dal.get_group_by_name(group_name)
                if not group:
                    raise HTTPException(status_code=404,
                                        detail=f"Группа с названием {group_name} не найдена")

                group_year = int("20" + group.group_name[:2]) # 23ISP1 => "20" + 23 = 2023
                speciality_code = group.speciality_code

                # Get plan for this group
                plan = await plan_dal.get_plan_by_year_and_speciality(group_year, speciality_code)
                if not plan:
                     raise HTTPException(status_code=404, detail=f"Учебный план не найден для года {group_year}, специальности {speciality_code}")

                # Get the number of work weeks this semester for this group.
                weeks = await semester_dal.get_semester_by_semester_and_plan(semester, plan.id)
                if not weeks:
                    raise HTTPException(status_code=404, detail=f"Для группы: {group_name} с планом: {plan.id} в этом семестре: {semester} ещё не сформировано рабочее кол-во недель")

                # Get subjects and teachers info
                subject_info = await get_info_for_subjects(plan.id)

                return {
                    "group": group_name,
                    "weeks": weeks,
                    "plan_id": plan.id,
                    "subjects_and_teachers": subject_info,
                }


    async def _delete_subject_in_cycle(self, subject_in_cycle_id: int, request: Request, db) -> ShowSubjectsInCycleWithHATEOAS:
            async with db as session:
                try:
                    async with session.begin():
                        subject_in_cycle_dal = SubjectsInCycleDAL(session)

                        if not await ensure_subject_in_cycle_exists(subject_in_cycle_dal, subject_in_cycle_id):
                            raise HTTPException(status_code=404, detail=f"Предмет в цикле с id {subject_in_cycle_id} не найден")

                        subject_in_cycle = await subject_in_cycle_dal.delete_subject_in_cycle(subject_in_cycle_id)

                        if not subject_in_cycle:
                            raise HTTPException(status_code=404, detail=f"Предмет в цикле с id {subject_in_cycle_id} не найден")

                        subject_in_cycle_pydantic = ShowSubjectsInCycle.model_validate(subject_in_cycle, from_attributes=True)

                        base_url = str(request.base_url).rstrip('/')
                        api_prefix = ''
                        api_base_url = f'{base_url}{api_prefix}'

                        hateoas_links = {
                            "subjects_in_cycles": f'{api_base_url}/subjects_in_cycles',
                            "create": f'{api_base_url}/subjects_in_cycles/create',
                            "cycle": f'{api_base_url}/cycles/search/by_id/{subject_in_cycle.cycle_in_chapter_id}',
                            "module": f'{api_base_url}/modules/search/by_id/{subject_in_cycle.module_in_cycle_id}' if subject_in_cycle.module_in_cycle_id else None
                        }
                        hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                        return ShowSubjectsInCycleWithHATEOAS(subject_in_cycle=subject_in_cycle_pydantic, links=hateoas_links)

                except HTTPException:
                    await session.rollback()
                    raise
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Неожиданная ошибка при удалении предмета в цикле {subject_in_cycle_id}: {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении предмета в цикле.")


    async def _update_subject_in_cycle(self, body: UpdateSubjectsInCycle, request: Request, db) -> ShowSubjectsInCycleWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["subject_in_cycle_id"]}
                    if "module_in_cycle_id" in update_data:
                        module_id_to_check = update_data["module_in_cycle_id"]
                        if module_id_to_check is not None:
                            module_dal = ModuleDAL(session)
                            cycle_id_to_check = update_data.get("cycle_in_chapter_id", body.cycle_in_chapter_id)
                            module_obj = await module_dal.get_module_by_id(module_id_to_check)

                            if module_obj.cycle_in_chapter_id != cycle_id_to_check:
                                raise HTTPException(status_code=400, detail=f"Модуль с id {module_id_to_check} не принадлежит циклу с id {cycle_id_to_check}")
                        else:
                            cycle_id_to_check = update_data.get("cycle_in_chapter_id", body.cycle_in_chapter_id)

                    elif "cycle_in_chapter_id" in update_data:
                        if update_data.get("module_in_cycle_id") is None:
                            cycle_id_to_check = update_data["cycle_in_chapter_id"]
                            
                            
                    subject_in_cycle_dal = SubjectsInCycleDAL(session)

                    if not await ensure_subject_in_cycle_exists(subject_in_cycle_dal, body.subject_in_cycle_id):
                        raise HTTPException(status_code=404, detail=f"Предмет в цикле с id {body.subject_in_cycle_id} не найден")

                    subject_in_cycle = await subject_in_cycle_dal.update_subject_in_cycle(target_id=body.subject_in_cycle_id, **update_data)
                    if not subject_in_cycle:
                        raise HTTPException(status_code=404, detail=f"Предмет в цикле с id {body.subject_in_cycle_id} не найден")

                    subject_in_cycle_id = subject_in_cycle.id 
                    subject_in_cycle_pydantic = ShowSubjectsInCycle.model_validate(subject_in_cycle, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/subjects_in_cycles/search/by_id/{subject_in_cycle_id}',
                        "update": f'{api_base_url}/subjects_in_cycles/update',
                        "delete": f'{api_base_url}/subjects_in_cycles/delete/{subject_in_cycle_id}',
                        "subjects_in_cycles": f'{api_base_url}/subjects_in_cycles',
                        "cycle": f'{api_base_url}/cycles/search/by_id/{subject_in_cycle.cycle_in_chapter_id}',
                        "module": f'{api_base_url}/modules/search/by_id/{subject_in_cycle.module_in_cycle_id}' if subject_in_cycle.module_in_cycle_id else None,
                        "hours": f'{api_base_url}/subjects_in_cycles_hours/search/by_subject_in_cycle/{subject_in_cycle_id}',
                        "streams": f'{api_base_url}/streams/search/by_subject_in_cycle/{subject_in_cycle_id}'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowSubjectsInCycleWithHATEOAS(subject_in_cycle=subject_in_cycle_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.warning(f"Изменение данных о предмете в цикле отменено (Ошибка: {e})")
                raise e
