from api.services_helpers import ensure_group_exists
from api.session.session_DAL import SessionDAL
from api.group.group_DAL import GroupDAL
from api.teacher_in_plan.teacher_in_plan_DAL import TeacherInPlanDAL
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from config.logging_config import configure_logging

from api.schedule.generate_doc import generate_schedule

from datetime import timedelta

# Create logger object
logger = configure_logging()


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
                    delta = timedelta(days=6)
                    end_period_date = start_period_date + delta

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