import logging
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List

from api.certification.certification_DAL import CertificationDAL
from api.chapter.chapter_DAL import ChapterDAL
from api.cycle.cycle_DAL import CycleDAL
from api.module.module_DAL import ModuleDAL
from api.plan.plan_DAL import PlanDAL
from api.semester.semester_DAL import SemesterDAL
from api.subject_in_cycle.subject_in_cycle_DAL import SubjectsInCycleDAL
from api.subject_in_cycle_hours.subject_in_cycle_hours_DAL import SubjectsInCycleHoursDAL

from config.logging_config import configure_logging

# Create logger object
logger = configure_logging()

class PersistenceService:
    """
    Сервис для сохранения спарсенных данных в базу данных.
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        # Инициализируем DAL'ы
        self.plan_dal = PlanDAL(db_session)
        self.chapter_dal = ChapterDAL(db_session)
        self.cycle_dal = CycleDAL(db_session)
        self.module_dal = ModuleDAL(db_session)
        self.subject_dal = SubjectsInCycleDAL(db_session)
        self.hours_dal = SubjectsInCycleHoursDAL(db_session)
        self.certification_dal = CertificationDAL(db_session)
        self.semester_dal = SemesterDAL(db_session)

    async def save_parsed_data(self, parsed_data: Dict[str, Any]) -> int:
        logger.info("Начинается сохранение спарсенных данных в БД.")

        plan = await self.plan_dal.create_plan(
            year=parsed_data['year'],
            speciality_code=parsed_data['speciality_code']
        )
        plan_id = plan.id
        logger.info(f"Создан план с ID: {plan_id}")

        for sem_data in parsed_data.get('semesters', []):
            await self.semester_dal.create_semester(
                semester=sem_data['semester'],
                weeks=sem_data['weeks'],
                practice_weeks=sem_data['practice_weeks'],
                plan_id=plan_id
            )
        logger.info(f"Сохранены семестры для плана {plan_id}")

        chapter_mapping = {}
        for chap_data in parsed_data.get('chapters', []):
            chapter = await self.chapter_dal.create_chapter(
                code=chap_data['code'],
                name=chap_data['name'],
                plan_id=plan_id
            )
            chapter_mapping[chap_data['id']] = chapter.id
        logger.info(f"Сохранены разделы (chapters) для плана {plan_id}")

        cycle_mapping = {}
        for chap_data in parsed_data.get('chapters', []):
            for cyc_data in chap_data.get('cycles', []):
                chapter_in_plan_id = chapter_mapping[chap_data['id']]
                cycle = await self.cycle_dal.create_cycle(
                    contains_modules=cyc_data.get('contains_modules'),
                    code=cyc_data['code'],
                    name=cyc_data['name'],
                    chapter_in_plan_id=chapter_in_plan_id
                )
                cycle_mapping[cyc_data['id']] = cycle.id
        logger.info(f"Сохранены циклы (cycles) для плана {plan_id}")

        module_mapping = {}
        for chap_data in parsed_data.get('chapters', []):
            for cyc_data in chap_data.get('cycles', []):
                for mod_data in cyc_data.get('modules', []):
                    cycle_in_chapter_id = cycle_mapping[cyc_data['id']]
                    module = await self.module_dal.create_module(
                        name=mod_data['name'],
                        code=mod_data['code'],
                        cycle_in_chapter_id=cycle_in_chapter_id
                    )
                    module_mapping[mod_data['id']] = module.id
        logger.info(f"Сохранены модули (modules) для плана {plan_id}")

        for chap_data in parsed_data.get('chapters', []):
            for cyc_data in chap_data.get('cycles', []):
                for sub_data in cyc_data.get('subjects', []):
                    if sub_data.get('module_in_cycle_id') is None:
                        logger.debug(f"Обработка предмета вне модуля: {sub_data['code']} (ID: {sub_data['id']})")

                        subject_title = sub_data['title']
                        if not subject_title:
                            subject_title = sub_data['code'] or "Без названия"
                            logger.warning(f"Предмет с кодом '{sub_data['code']}' (вне модуля) имеет пустое название. Используется: '{subject_title}'")

                        cycle_in_chapter_id = cycle_mapping[cyc_data['id']]
                        subject = await self.subject_dal.create_subject_in_cycle(
                            code=sub_data['code'],
                            title=subject_title,
                            cycle_in_chapter_id=cycle_in_chapter_id,
                            module_in_cycle_id=None 
                        )
                        subject_in_cycle_id = subject.id
                        logger.debug(f"Создан предмет '{sub_data['code']}' (вне модуля) с ID {subject_in_cycle_id} для цикла {cycle_in_chapter_id}")

                        await self._save_hours_and_certifications(sub_data, subject_in_cycle_id)
                        logger.debug(f"Завершена обработка часов и аттестаций для предмета '{sub_data['code']}' (ID: {subject_in_cycle_id})")

                for mod_data in cyc_data.get('modules', []):
                    cycle_in_chapter_id = cycle_mapping[cyc_data['id']]
                    module_in_cycle_id = module_mapping[mod_data['id']]
                    for sub_data in mod_data.get('subjects', []):
                        if sub_data.get('module_in_cycle_id') is not None:
                            logger.debug(f"Обработка предмета в модуле: {sub_data['code']} (ID: {sub_data['id']})")

                            subject_title = sub_data['title']
                            if not subject_title:
                                subject_title = sub_data['code'] or "Без названия"
                                logger.warning(f"Предмет с кодом '{sub_data['code']}' (в модуле) имеет пустое название. Используется: '{subject_title}'")

                            subject = await self.subject_dal.create_subject_in_cycle(
                                code=sub_data['code'],
                                title=subject_title,
                                cycle_in_chapter_id=None, 
                                module_in_cycle_id=module_in_cycle_id
                            )
                            subject_in_cycle_id = subject.id
                            logger.debug(f"Создан предмет '{sub_data['code']}' (в модуле) с ID {subject_in_cycle_id} для модуля {module_in_cycle_id}")

                            await self._save_hours_and_certifications(sub_data, subject_in_cycle_id)
                            logger.debug(f"Завершена обработка часов и аттестаций для предмета '{sub_data['code']}' (ID: {subject_in_cycle_id})")

        logger.info(f"Сохранение предметов, часов и аттестаций завершено для плана {plan_id}")
        logger.info("Сохранение спарсенных данных в БД завершено успешно.")
        return plan_id

    async def _save_hours_and_certifications(self, subject_data: Dict[str, Any], subject_in_cycle_id: int):
        """
        Вспомогательный метод для сохранения часов и аттестаций для одного предмета.
        """
        logger.debug(f"Сохранение часов для subject_in_cycle_id {subject_in_cycle_id}, количество записей: {len(subject_data.get('hours', []))}")
        for hour_data in subject_data.get('hours', []):
            logger.debug(f"Создание часов для семестра {hour_data['semester']}, subject_in_cycle_id {subject_in_cycle_id}")
            hours_obj = await self.hours_dal.create_subject_in_cycle_hours(
                semester=hour_data['semester'],
                self_study_hours=hour_data.get('self_study_hours', 0),
                lectures_hours=hour_data.get('lectures_hours', 0),
                laboratory_hours=hour_data.get('laboratory_hours', 0),
                practical_hours=hour_data.get('practical_hours', 0),
                course_project_hours=hour_data.get('course_project_hours', 0),
                consultation_hours=hour_data.get('consultation_hours', 0),
                intermediate_assessment_hours=hour_data.get('intermediate_assessment_hours', 0),
                subject_in_cycle_id=subject_in_cycle_id
            )
            logger.debug(f"Создана запись часов с ID {hours_obj.id}")

            for cert_data in subject_data.get('certifications', []):
                if cert_data['semester'] == hour_data['semester']:
                    logger.debug(f"Создание аттестации для семестра {cert_data['semester']}, subject_in_cycle_hours_id {hours_obj.id}")
                    await self.certification_dal.create_certification(
                        id=hours_obj.id,
                        credit=cert_data.get('credit', False),
                        differentiated_credit=cert_data.get('differentiated_credit', False),
                        course_project=cert_data.get('course_project', False),
                        course_work=cert_data.get('course_work', False),
                        control_work=cert_data.get('control_work', False),
                        other_form=cert_data.get('other_form', False),
                    )
                    logger.debug(f"Создана аттестация для subject_in_cycle_hours_id {hours_obj.id}")
