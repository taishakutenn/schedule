from api.services_helpers import ensure_group_exists
from api.session.session_DAL import SessionDAL
from api.group.group_DAL import GroupDAL
from api.teacher_in_plan.teacher_in_plan_DAL import TeacherInPlanDAL
from fastapi import HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

from config.logging_config import configure_logging

from api.schedule.generate_doc import generate_schedule

from datetime import timedelta, date

# Create logger object
logger = configure_logging()


def calculate_end_period_date(start_period_date: date, count_days: int) -> date:
    # Give end range days
    delta = timedelta(days=count_days)
    end_period_date = start_period_date + delta
    return end_period_date


class ScheduleService:
    async def _get_sessions_report_by_group(self, group_name, start_period_date, db):
        async with db as session:
            async with session.begin():
                try:
                    group_dal = GroupDAL(db)
                    teacher_in_plan_dal = TeacherInPlanDAL(db)
                    session_dal = SessionDAL(db)

                    group = await ensure_group_exists(group_dal, group_name)
                    if not group:
                        raise HTTPException(status_code=404, detail=f"Группа с таким названием: {group_name} не существует")

                    # Get all teacher_in_plan_id from group_name
                    teachers_in_plan = await teacher_in_plan_dal.get_teachers_in_plans_by_group(group_name, page=0, limit=10)
                    teachers_in_plan_ids = [teacher.teacher_id for teacher in teachers_in_plan]

                    # Give end range days
                    end_period_date = calculate_end_period_date(start_period_date, 6)

                    # Get session
                    sessions = await session_dal.get_sessions_by_teacher_in_plan_and_date(teachers_in_plan_ids,
                                                                                          start_period_date,
                                                                                          end_period_date)
                    if not sessions:
                        raise HTTPException(status_code=404,
                                            detail=f"Для группы: {group_name} на неделю с начала даты: {start_period_date} не найдено учебных занятий")

                    # Generate docx
                    created_docx = await generate_schedule(group_name, sessions, start_period_date, db) # -> return stream

                    return StreamingResponse(
                        created_docx,
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        headers={"Content-Disposition": f"attachment; filename=schedule.docx"}
                    )

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение документа отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")

    async def _copy_all_schedule(self, start_copy_period_date: date, start_period_date: date, count_days: int, db):
        """
        start_copy_period_date - первый день диапазона, с которого будем копировать расписание
        start_period_date - первый день диапазона, на который будем копировать расписание
        count_days - количество дней для копирования
        """
        async with db as session:
            async with session.begin():
                try:
                    session_dal = SessionDAL(db)

                    # Рассчитываем конечные даты диапазонов
                    end_period_copy_date = calculate_end_period_date(start_copy_period_date, count_days)
                    end_period_date = calculate_end_period_date(start_period_date, count_days)

                    # Получаем сессии, которые будем копировать
                    copied_sessions = await session_dal.get_sessions_by_date_range(start_copy_period_date, end_period_copy_date)
                    if not copied_sessions:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Расписание за период с {start_copy_period_date} по {end_period_copy_date} не найдено"
                        )

                    # Проверяем, есть ли уже расписание на новый период
                    existing_sessions = await session_dal.get_sessions_by_date_range(start_period_date, end_period_date)
                    if existing_sessions:
                        raise HTTPException(
                            status_code=409,
                            detail=f"На период с {start_period_date} по {end_period_date} расписание уже существует"
                        )

                    # Вычисляем разницу в днях для сдвига дат
                    days_diff = (start_period_date - start_copy_period_date).days

                    # Копируем каждую сессию с новой датой
                    for old_session in copied_sessions:
                        new_date = old_session.date + timedelta(days=days_diff)
                        await session_dal.create_session(
                            session_number=old_session.session_number,
                            session_date=new_date,
                            teacher_in_plan=old_session.teacher_in_plan,
                            session_type=old_session.session_type,
                            cabinet_number=old_session.cabinet_number,
                            building_number=old_session.building_number
                        )

                    return {"message": f"Расписание успешно скопировано с {start_copy_period_date} на {start_period_date}"}

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Копирование расписания отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при копировании расписания.")