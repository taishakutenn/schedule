from io import BytesIO

from docxtpl import DocxTemplate
from datetime import timedelta, date, datetime

from config.settings import ROOT_PATH

from config.logging_config import configure_logging
from api.teacher.teacher_DAL import TeacherDAL
from api.teacher_in_plan.teacher_in_plan_DAL import TeacherInPlanDAL
from api.subject_in_cycle_hours.subject_in_cycle_hours_DAL import SubjectsInCycleHoursDAL
from api.subject_in_cycle.subject_in_cycle_DAL import SubjectsInCycleDAL

# Create logger object
logger = configure_logging()


async def generate_schedule(group_name, sessions_data, start_period_date: date, db):
    # Расчитываем дату
    delta = timedelta(days=6)
    end_period_date = start_period_date + delta

    # Заполняем контекст
    context = await generate_sessions_context(sessions_data, db)
    context["start_period_date"] = start_period_date
    context["end_period_date"] = end_period_date
    context["group_name"] = group_name

    # Opening and rendering template
    doc = DocxTemplate(f"{ROOT_PATH}/api/schedule/templates/template_schedule.docx")
    doc.render(context)

    # Create object in memory
    file_stream = BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)

    return file_stream


async def generate_sessions_context(data, db):
    # Проходимся по каждой сессии, определяем её день недели и номер пары, составляем строку с информацией,
    # вставляем эту строку в переменную с название, содержащим день недели и номер пары
    days_with_numbers_dict = {
        0: "monday",
        1: "tuesday",
        2: "wednesday",
        3: "thursday",
        4: "friday",
        5: "saturday"
    }

    context = {}

    # Create dals
    teacher_dal = TeacherDAL(db)
    teacher_in_plan_dal = TeacherInPlanDAL(db)
    subject_in_cycle_hours_dal = SubjectsInCycleHoursDAL(db)
    subject_in_cycle_dal = SubjectsInCycleDAL(db)

    # Для кажого занятия определяем день недели
    for session in data:
        current_day = days_with_numbers_dict[session.date.weekday()]  # Получаем число дня недели и используем как ключ
        current_session_number = session.session_number

        # Из дня недели и номера пары формируем строки, которые будет ключами контекста для docx документа
        context_session = f"{current_day}_{current_session_number}_session"
        context_cabinet = f"{current_day}_{current_session_number}_cabinet"

        # Формируем итоговые строки, которые будут записаны в документ по созданым нами ключа

        # Получаем данные о преподе
        current_teacher_in_plan = await teacher_in_plan_dal.get_teacher_in_plan_by_id(session.teacher_in_plan)
        current_teacher = await teacher_dal.get_teacher_by_id(current_teacher_in_plan.teacher_id)
        current_teacher_fio = (f"{current_teacher.surname} {current_teacher.name[:1]}."
                               f"{current_teacher.fathername[:1]}.")
        current_teacher_category = current_teacher.teacher_category

        # Получаем данные о предмете
        subject_hours = await subject_in_cycle_hours_dal.get_subject_in_cycle_hours_by_id(
            current_teacher_in_plan.subject_in_cycle_hours_id)
        subject = await subject_in_cycle_dal.get_subject_in_cycle_by_id(subject_hours.subject_in_cycle_id)

        session_info = (f"{subject.title}, {session.session_type},"
                        f" {current_teacher_fio}, {current_teacher_category}")
        cabinet_info = f"{session.building_number}-{session.cabinet_number}"

        # Теперь записываем данные в контекст
        context[context_session] = session_info
        context[context_cabinet] = cabinet_info

    return context

# session_number=1 session_date=datetime.date(2025, 12, 4) teacher_in_plan=1 session_type='Лб' cabinet_number=215 building_number=2
# session_number=2 session_date=datetime.date(2025, 12, 4) teacher_in_plan=1 session_type='Лб' cabinet_number=215 building_number=2
# session_number=3 session_date=datetime.date(2025, 12, 4) teacher_in_plan=1 session_type='Лб' cabinet_number=215 building_number=2
# session_number=1 session_date=datetime.date(2025, 12, 5) teacher_in_plan=3 session_type='Лб' cabinet_number=215 building_number=2
# session_number=3 session_date=datetime.date(2025, 12, 5) teacher_in_plan=2 session_type='Лб' cabinet_number=215 building_number=2
# session_number=2 session_date=datetime.date(2025, 12, 6) teacher_in_plan=4 session_type='Лб' cabinet_number=215 building_number=2
# session_number=2 session_date=datetime.date(2025, 12, 6) teacher_in_plan=3 session_type='Лб' cabinet_number=215 building_number=2
# session_number=3 session_date=datetime.date(2025, 12, 6) teacher_in_plan=2 session_type='Лб' cabinet_number=215 building_number=2
# session_number=1 session_date=datetime.date(2025, 12, 1) teacher_in_plan=1 session_type='Лб' cabinet_number=215 building_number=2
# session_number=2 session_date=datetime.date(2025, 12, 1) teacher_in_plan=2 session_type='Лб' cabinet_number=215 building_number=2
# session_number=3 session_date=datetime.date(2025, 12, 1) teacher_in_plan=3 session_type='Лб' cabinet_number=215 building_number=2
# session_number=1 session_date=datetime.date(2025, 12, 2) teacher_in_plan=3 session_type='Лб' cabinet_number=215 building_number=2
# session_number=1 session_date=datetime.date(2025, 12, 2) teacher_in_plan=4 session_type='Лб' cabinet_number=215 building_number=2
# session_number=2 session_date=datetime.date(2025, 12, 2) teacher_in_plan=3 session_type='Лб' cabinet_number=215 building_number=2
# session_number=3 session_date=datetime.date(2025, 12, 2) teacher_in_plan=1 session_type='Лб' cabinet_number=215 building_number=2
# session_number=4 session_date=datetime.date(2025, 12, 3) teacher_in_plan=1 session_type='Лб' cabinet_number=215 building_number=2
