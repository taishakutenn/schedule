"""
File for encapsulating business logic,
here classes are written for implementing crud operations for each table.
There is no need to do checks in the data,
because it is assumed that the data submitted here is already validated.
"""

from typing import Optional

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import ShowTeacher, ShowBuilding, ShowCabinet, ShowSpeciality, ShowGroup, ShowCurriculum
from db.models import Teacher, Group, Cabinet, Building, Speciality, Curriculum
from config.logging_config import configure_logging

# Сreate logger object
logger = configure_logging()


'''
================
DAL for Teacher
================
'''


class TeacherDAL:
    """Data Access Layer for operating teacher info"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session


    async def create_teacher(
            self, name: str, surname: str, phone_number: str, email: str = None, fathername: str = None
    ) -> Teacher:
        new_teacher = Teacher(
            name=name,
            surname=surname,
            phone_number=phone_number,
            email=email,
            fathername=fathername
        )

        # Add teacher in session
        self.db_session.add(new_teacher)

        # Add changes to the database, but do not commit them strictly
        await self.db_session.flush()

        logger.info(f"Новый учитель успешно добавлен в бд")
        return new_teacher


    async def delete_teacher(self, id: int) -> ShowTeacher | None:
        # Сначала находим учителя по id
        query_select = select(Teacher).where(Teacher.id == id)
        res = await self.db_session.execute(query_select)
        teacher = res.scalar_one_or_none()

        if teacher is None:
            logger.warning(f"Не было найдено ни одного учителя с таким id: {id}")
            return None

        # Удаляем учителя
        query_delete = delete(Teacher).where(Teacher.id == id)
        await self.db_session.execute(query_delete)

        logger.info(f"Учитель с id {id} был успешно удалён из бд")

        return ShowTeacher(
            name=teacher.name,
            surname=teacher.surname,
            phone_number=teacher.phone_number,
            email=teacher.email,
            fathername=teacher.fathername
        )


    async def get_all_teachers(self, page: int, limit: int) -> list[ShowTeacher] | None:
        # Calculate first and end selection element.
        # Based on the received page and elements on it
        # If the page is zero - then select all elements

        if page == 0:
            query = select(Teacher).order_by(Teacher.surname.asc())
        else:
            query = (
                select(Teacher)
                .offset((page - 1) * limit)
                .limit(limit)
            )

        result = await self.db_session.execute(query)
        teachers = result.scalars().all()

        if teachers:
            logger.info(f"Найдено учителей: {len(teachers)}")
            return [
                ShowTeacher(
                    name=t.name,
                    surname=t.surname,
                    email=t.email,
                    phone_number=t.phone_number,
                    fathername=t.fathername
                ) for t in teachers
            ]

        logger.warning("Не было найдено ни одного учителя")
        return None


    async def get_teacher_by_id(self, id) -> Teacher | None:
        query = select(Teacher).where(Teacher.id == id)
        res = await self.db_session.execute(query)  # Make an asynchronous query to the database to search for a teacher
        teacher_row = res.scalar()  # return object Teacher or None
        if teacher_row is not None:
            logger.info(f"Учитель с id: {id} был успешно найден")
            return Teacher(
                name=teacher_row.name,
                surname=teacher_row.surname,
                phone_number=teacher_row.phone_number,
                email=teacher_row.email,
                fathername=teacher_row.fathername
            )

        logger.warning(f"Не было найдено ни одного учителя с таким id: {id}")
        return None


    async def get_teacher_by_name_surname(self, name: str, surname: str) -> Teacher | None:
        query = select(Teacher).where(
            (Teacher.name == name) & (Teacher.surname == surname)
        )
        res = await self.db_session.execute(query)
        teacher_row = res.scalar()  # return object Teacher or None
        if teacher_row is not None:
            logger.info(f"Учитель с ФИ: {name} - {surname} был успешно найден")
            return Teacher(
                name=teacher_row.name,
                surname=teacher_row.surname,
                phone_number=teacher_row.phone_number,
                email=teacher_row.email,
                fathername=teacher_row.fathername
            )

        logger.warning(f"Не было найдено ни одного учителя с таким ФИ: {name} - {surname}")
        return None


    async def update_teacher(self, id, **kwargs) -> Optional[Teacher]:
        query = (
            update(Teacher)
            .where(Teacher.id == id)
            .values(**kwargs)
            .returning(Teacher)
        )
        res = await self.db_session.execute(query)
        updated_teacher = res.scalar()
        if updated_teacher:
            logger.info(f"У учителя с id: {id} были успешно обновлены поля: {{{', '.join(kwargs.keys())}}}")
            return updated_teacher

        logger.warning(f"Не было найдено ни одного учителя с таким id: {id}")
        return None


'''
================
DAL for Building
================
'''


class BuildingDAL:
    """Data Access Layer for operating building info"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session


    async def create_building(
            self, building_number: int, city: str, building_address: str
    ) -> Building:
        new_building = Building(
            building_number=building_number,
            city=city,
            building_address=building_address
        )

        # Add building in session
        self.db_session.add(new_building)

        # Add changes to the database, but do not commit them strictly
        await self.db_session.flush()

        logger.info("Новое здание успешно добавлено в бд")
        return new_building

    async def delete_building(self, building_number: int) -> bool:
        query = delete(Building).where(Building.building_number == building_number).returning(Building.building_number)
        res = await self.db_session.execute(query)
        deleted_building = res.fetchone()
        if not deleted_building:  # if there aren't deleted records
            logger.warning(f"Не было найдено ни одного здания с таким номером: {building_number}")
            return False
        logger.info(f"Здание с номером: {building_number} было успешно удалено из бд")
        return True

    async def get_all_buildings(self, page: int, limit: int) -> list[ShowBuilding] | None:
        # Calculate first and end selection element.
        # Based on the received page and elements on it
        # If the page is zero - then select all elements

        if page == 0:
            query = select(Building).order_by(Building.building_number.asc())
        else:
            query = (
                select(Building)
                .offset((page - 1) * limit)
                .limit(limit)
            )

        result = await self.db_session.execute(query)
        buildings = result.scalars().all()

        if buildings:
            logger.info(f"Найдено зданий: {len(buildings)}")
            return [
                ShowBuilding(
                    building_number=b.building_number,
                    city=b.city,
                    building_address=b.building_address
                ) for b in buildings
            ]

        logger.warning("Не было найдено ни одного здания")
        return None


    async def get_building_by_number(self, building_number: int) -> Building | None:
        query = select(Building).where(Building.building_number == building_number)
        res = await self.db_session.execute(
            query)  # Make an asynchronous query to the database to search for a building
        building_row = res.scalar()  # return object Building or None
        if building_row is not None:
            logger.info(f"Здание с номером: {building_number} было успешно найдено")
            return Building(
                building_number=building_row.building_number,
                city=building_row.city,
                building_address=building_row.building_address
            )
        logger.warning(f"Не было найдено ни одного здания с номером: {building_number}")
        return None


    async def get_building_by_address(self, building_address: str) -> Building | None:
        query = select(Building).where(Building.building_address == building_address)
        res = await self.db_session.execute(
            query)  # Make an asynchronous query to the database to search for a building
        building_row = res.scalar()  # return object Building or None
        if building_row is not None:
            logger.info(f"Здание по адресу: {building_address} было успешно найдено")
            return Building(
                building_number=building_row.building_number,
                city=building_row.city,
                building_address=building_row.building_address
            )

        logger.warning(f"Не было найдено ни одного здания по адресу: {building_address}")
        return None

    async def update(self, building_number: int, **kwargs) -> Optional[int]:
        query = (
            update(Building).
            where(Building.building_number == building_number).
            values(**kwargs).
            returning(Building.building_number)
        )
        res = await self.db_session.execute(query)
        update_building = res.scalar()  # return Group name or None
        if update_building is not None:
            logger.info(
                f"Для здания с номером: {building_number}. Были успешно обновлены поля: {" - ".join(kwargs.keys())}")
            return update_building.group_name
        logger.warning(f"Не было найдено ни однго здания под номером: {building_number}")
        return None

    async def update_building(self, building_number, **kwargs) -> Optional[Building]:


    async def update_building(self, building_number, **kwargs) -> Building | None:
        query = (
            update(Building)
            .where(Building.building_number == building_number)
            .values(**kwargs)
            .returning(Building)
        )
        res = await self.db_session.execute(query)
        updated_building = res.scalar()
        if updated_building:
            logger.info(
                f"У здания с номером: {building_number} были успешно обновлены поля: {{{', '.join(kwargs.keys())}}}")
            return updated_building

        logger.warning(f"Не было найдено ни одного здания с номером: {building_number}")
        return None


'''
===============
DAL for Cabinet
===============
'''


class CabinetDAL:
    """Data Access Layer for operating cabinet info"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session


    async def create_cabinet(
            self, cabinet_number: int, building_number: int, capacity: int = None, cabinet_state: str = None,
    ) -> Cabinet:

        new_cabinet = Cabinet(
            cabinet_number=cabinet_number,
            capacity=capacity,
            cabinet_state=cabinet_state,
            building_number=building_number
        )

        # Add cabinet in session
        self.db_session.add(new_cabinet)

        # Add changes to the database, but do not commit them strictly
        await self.db_session.flush()

        logger.info("Новый кабинет успешно добавлен в бд")
        return new_cabinet

    async def delete_cabinet(self, building_number: int, cabinet_number: int) -> Cabinet | False:
        query = delete(Cabinet).where(
            (Cabinet.cabinet_number == cabinet_number) & (Cabinet.building_number == building_number)).returning(
            Cabinet)
        res = await self.db_session.execute(query)
        deleted_cabinet = res.fetchone()
        if not deleted_cabinet:  # if there aren't deleted records
            logger.warning(f"Не было найдено ни одного кабинета с таким номером: {cabinet_number}")
            return False

        logger.info(f"Кабинет с номером: {cabinet_number} в здании: {building_number} - был успешно удален из бд")
        return deleted_cabinet

    async def get_cabinet(self, cabinet_number: int) -> Optional[Cabinet]:
        query = select(Cabinet).where(Cabinet.cabinet_number == cabinet_number)
        res = await self.db_session.execute(query)  # Make an asynchronous query to the database to search for a cabinet
        cabinet_row = res.scalar()  # return object Cabinet or None
        if cabinet_row is not None:
            logger.info(f"Кабинет с номером: {cabinet_number} был успешно найден")
            return cabinet_row.id
        logger.warning(f"Не было найдено ни одного кабинета с номером: {cabinet_number}")
        return None

    async def get_cabinet_by_number_and_building(self, building_number: int, cabinet_number: int) -> Cabinet | None:
        query = select(Cabinet).where(
            (Cabinet.cabinet_number == cabinet_number) &
            (Cabinet.building_number == building_number)
        )
        res = await self.db_session.execute(query)

        cabinet = res.scalar_one_or_none()
        if not cabinet:
            logger.error(f"Кабинет с номером: {cabinet_number} в здании с номером: {building_number} - не найден")
            return None

        return cabinet

    async def get_all_cabinets(self, page: int, limit: int) -> list[ShowCabinet] | None:
        # Calculate first and end selection element.
        # Based on the received page and elements on it
        # If the page is zero - then select all elements

        if page == 0:
            query = select(Cabinet).order_by(Cabinet.cabinet_number.asc())
        else:
            query = (
                select(Cabinet)
                .offset((page - 1) * limit)
                .limit(limit)
            )

        result = await self.db_session.execute(query)
        cabinets = result.scalars().all()

        if cabinets:
            logger.info(f"Найдено кабинетов: {len(cabinets)}")
            return [
                ShowCabinet(
                    cabinet_number=c.cabinet_number,
                    capacity=c.capacity,
                    cabinet_state=c.cabinet_state,
                    building_number=c.building_number
                ) for c in cabinets
            ]
        else:
            logger.error("Не было найдено ни одного кабинета")
            return None

    async def get_cabinets_by_building(self, building_number: int,
                                       page: int,
                                       limit: int) -> list[ShowCabinet] | None:
        if page == 0:
            query = select(Cabinet).where(Cabinet.building_number == building_number).order_by(
                Cabinet.cabinet_number.asc())
        else:
            query = (
                select(Cabinet)
                .where(Cabinet.building_number == building_number)
                .offset((page - 1) * limit)
                .limit(limit)
            )

        result = await self.db_session.execute(query)
        cabinets = result.scalars().all()

        if cabinets:
            logger.info(f"Найдено кабинетов: {len(cabinets)}")
            return [
                ShowCabinet(
                    cabinet_number=c.cabinet_number,
                    capacity=c.capacity,
                    cabinet_state=c.cabinet_state,
                    building_number=c.building_number
                ) for c in cabinets
            ]
        else:
            logger.warning(f"Не было найдено ни одного кабинета в здании с номером: {building_number}")
            return None

    async def update(self, cabinet_number: int, **kwargs) -> Optional[int]:

        logger.warning("Не было найдено ни одного кабинета")
        return None


    async def update(self, cabinet_number: int, **kwargs) -> Cabinet:
        query = (
            update(Cabinet).
            where(Cabinet.cabinet_number == cabinet_number).
            values(**kwargs).
            returning(Cabinet.cabinet_number)
        )
        res = await self.db_session.execute(query)
        update_cabinet = res.scalar()  # return Cabinet name or None
        if update_cabinet is not None:
            logger.info(
                f"Для кабнета с номером: {cabinet_number}. Были успешно обновлены поля: {" - ".join(kwargs.keys())}")
            return update_cabinet.group_name
            logger.info(f"Для кабнета с номером: {cabinet_number}. Были успешно обновлены поля: {" - ".join(kwargs.keys())}")
            return update_cabinet

        logger.warning(f"Не было найдено ни одного кабинета с таким номером: {cabinet_number}")
        return None

# '''
# ==============
# DAL for Group
# ==============
# '''

'''
==================
DAL for Speciality
==================
'''

class SpecialityDAL:
    """Data Access Layer for operating speciality info"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session


    async def create_speciality(self, speciality_code: str) -> Cabinet:

        new_speciality = Speciality(speciality_code)

        # Add speciality in session
        self.db_session.add(new_speciality)

        # Add changes to the database, but do not commit them strictly
        await self.db_session.flush()
        logger.info("Новая сециальность добавлена в бд")
        return new_speciality


    async def delete_speciality(self, speciality_code: str) -> Speciality | None:
        query_select = select(Speciality).where(Speciality.speciality_code == speciality_code)
        res = await self.db_session.execute(query_select)
        speciality = res.scalar_one_or_none()

        if speciality is None:
            return None

        query_delete = delete(Speciality).where(Speciality.speciality_code == speciality_code)
        await self.db_session.execute(query_delete)

        logger.info(f"Специальность с кодом: {speciality_code} была успешно удаена из бд")

        return speciality


    async def get_all_speciality(self, page: int, limit: int) -> list[ShowSpeciality] | None:
        # Calculate first and end selection element.
        # Based on the received page and elements on it
        # If the page is zero - then select all elements

        if page == 0:
            query = select(Speciality).order_by(Speciality.speciality_code.asc())
        else:
            query = (
                select(Speciality)
                .offset((page - 1) * limit)
                .limit(limit)
            )

        result = await self.db_session.execute(query)
        specialities = result.scalars().all()

        if specialities:
            logger.info(f"Найдено специальностей: {len(specialities)}")
            return [
                ShowSpeciality(speciality_code=sp.speciality_code) for sp in specialities
            ]

        return None


    async def get_speciality_by_code(self, speciality_code) -> ShowSpeciality | None:
        query = select(Speciality).where(Speciality.speciality_code == speciality_code)
        res = await self.db_session.execute(query)  # Make an asynchronous query to the database to search for a speciality
        speciality_row = res.scalar()  # return object Speciality or None
        if speciality_row is not None:
            logger.info(f"специальность с кодом: {speciality_code} была успешно найдена")
            return speciality_row

        return None


    async def update_speciality(self, speciality_code, new_speciality_code) -> Speciality | None:
        query = (
            update(Speciality)
            .where(Speciality.speciality_code == speciality_code)
            .values(new_speciality_code)
            .returning(Speciality)
        )
        res = await self.db_session.execute(query)
        update_speciality = res.scalar()
        if update_speciality:
            logger.info(f"У специальности с кодом: {speciality_code} был успешно изменён код:  {new_speciality_code}")
            return update_speciality

        return None


'''
==============
DAL for Group
==============
'''

class GroupDAL:
    """Data Access Layer for operating group info"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session


    async def create_group(
            self, group_name: str, speciality_code: str, quantity_students: int = None, group_advisor_id: int = None,
    ) -> Group:
        new_group = Group(
            group_name=group_name,
            speciality_code=speciality_code,
            quantity_students=quantity_students,
            group_advisor_id=group_advisor_id,
        )

        # Add group in session
        self.db_session.add(new_group)

        # Add changes to the database, but do not commit them strictly
        await self.db_session.flush()
        logger.info("Новая группа успешно добавлена в бд")

        return new_group


    async def delete_group(self, group_name: str) -> Group | None:
        query = delete(Group).where(Group.group_name == group_name).returning(Group.group_name)
        res = await self.db_session.execute(query)
        deleted_group = res.fetchone()
        if not deleted_group:  # if there aren't deleted records
            logger.warning(f"Не было найдено ни одной группы с таким названием: {group_name}")
            return None

        logger.info(f"Группа с названием: '{group_name}' была успешно удалена из бд")
        return deleted_group


    async def get_group(self, group_name: str) -> Group | None:
        query = select(Group).where(Group.group_name == group_name)
        res = await self.db_session.execute(query)  # Make an asynchronous query to the database to search for a group
        group_row = res.scalar()  # return object Group or None
        if group_row is not None:
            logger.info(f"Группа с названием: '{group_name}' была успешно найдена")
            return group_row

        logger.warning(f"Не было найдено ни одной группы с названием: '{group_name}'")
        return None


    async def get_all_group(self, page: int, limit: int) -> list[ShowGroup] | None:
        # Calculate first and end selection element.
        # Based on the received page and elements on it
        # If the page is zero - then select all elements

        if page == 0:
            query = select(Group).order_by(Group.group_name.asc())
        else:
            query = (
                select(Group)
                .offset((page - 1) * limit)
                .limit(limit)
            )

        result = await self.db_session.execute(query)
        groups = result.scalars().all()

        if groups:
            logger.info(f"Найдено групп: {len(groups)}")
            return [
                ShowGroup(
                    group_name=gr.group_name,
                    speciality_code=gr.speciality_code,
                    quantity_students=gr.quantity_students,
                    group_advisor_id=gr.group_advisor_id
                ) for gr in groups
            ]

        logger.warning("Не было найдено ни однй группы")
        return None


    async def update(self, group_name: str, **kwargs) -> Group | None:
        query = (
            update(Group).
            where(Group.group_name == group_name).
            values(**kwargs).
            returning(Group.group_name)
        )
        res = await self.db_session.execute(query)
        update_group = res.scalar()  # return Group or None
        if update_group is not None:
            logger.info(f"Для группы с названием: '{group_name}'. Были успешно обновлены поля: {{{', '.join(kwargs.keys())}}}")
            return update_group

        logger.warning(f"Не было найдено ни одной группы с таким названием: '{group_name}'")
        return None


'''
==========
Curriculum
==========
'''


class CurriculumDAL:
    """Data Access Layer for operating curriculum info"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session


    async def create_curriculum(
            self, semester_number: int, group_name: str, subject_code: str,
                  lectures_hours: float = None, laboratory_hours: float = None, practical_hours: float = None
    ) -> Curriculum:
        new_curriculum = Curriculum(
            semester_number=semester_number,
            group_name=group_name,
            subject_code=subject_code,
            lectures_hours=lectures_hours,
            laboratory_hours=laboratory_hours,
            practical_hours=practical_hours
        )

        # Add teacher in session
        self.db_session.add(new_curriculum)

        # Add changes to the database, but do not commit them strictly
        await self.db_session.flush()

        logger.info(f"Новый уч.план успешно добавлен в бд")
        return new_curriculum


    async def delete_curriculum(self, semester_number: int, group_name: str, subject_code: str) -> ShowCurriculum | None:
        query_select = (
        select(Curriculum)
        .where(
            Curriculum.semester_number == semester_number,
            Curriculum.group_name == group_name,
            Curriculum.subject_code == subject_code
        )
    )
        res = await self.db_session.execute(query_select)
        curriculum = res.scalar_one_or_none()

        if curriculum is None:
            logger.warning(f"Не было найдено ни одного уч.плана с такими номером семестра: {semester_number}, именем группы: {group_name}, кодом предмета: {subject_code}")
            return None

        # Удаляем учителя
        query_delete = delete(Curriculum).where(
            Curriculum.semester_number == semester_number,
            Curriculum.group_name == group_name,
            Curriculum.subject_code == subject_code
        )
        await self.db_session.execute(query_delete)

        logger.info(f"Уч.плана с такими номером семестра: {semester_number}, именем группы: {group_name}, кодом предмета: {subject_code} был успешно удалён из бд")

        return ShowCurriculum(
            semester_number=curriculum.semester_number,
            group_name=curriculum.group_name,
            subject_code=curriculum.subject_code,
            lectures_hours=curriculum.lectures_hours,
            laboratory_hours=curriculum.laboratory_hours,
            practical_hours=curriculum.practical_hours
        )


    async def get_all_curriculums(self, page: int, limit: int) -> list[ShowCurriculum] | None:
        # Calculate first and end selection element.
        # Based on the received page and elements on it
        # If the page is zero - then select all elements

        if page == 0:
            query = select(Curriculum).order_by(Curriculum.semester_number.asc())
        else:
            query = (
                select(Curriculum)
                .offset((page - 1) * limit)
                .limit(limit)
            )

        result = await self.db_session.execute(query)
        curriculums = result.scalars().all()

        if curriculums:
            logger.info(f"Найдено уч.планов: {len(curriculums)}")
            return [
                ShowCurriculum(
                    semester_number=c.semester_number,
                    group_name=c.group_name,
                    subject_code=c.subject_code,
                    lectures_hours=c.lectures_hours,
                    laboratory_hours=c.laboratory_hours,
                    practical_hours=c.practical_hours
                ) for c in curriculums
            ]

        logger.warning("Не было найдено ни одного уч.плана")
        return None


    async def get_curriculum(self, semester_number: int, group_name: str, subject_code: str) -> Curriculum | None:
        query = select(Curriculum).where(
            Curriculum.semester_number == semester_number,
            Curriculum.group_name == group_name,
            Curriculum.subject_code == subject_code
        )
        res = await self.db_session.execute(query)  # Make an asynchronous query to the database to search for a teacher
        curriculum_row = res.scalar()  # return object Teacher or None
        if curriculum_row is not None:
            logger.info(f"Учитель с id: {id} был успешно найден")
            return Curriculum(
                semester_number=curriculum_row.semester_number,
                group_name=curriculum_row.group_name,
                subject_code=curriculum_row.subject_code,
                lectures_hours=curriculum_row.lectures_hours,
                laboratory_hours=curriculum_row.laboratory_hours,
                practical_hours=curriculum_row.practical_hours
            )

        logger.warning(f"Не было найдено ни одного учителя с таким id: {id}")
        return None


    # async def update_teacher(self, id, **kwargs) -> Optional[Teacher]:
    #     query = (
    #         update(Teacher)
    #         .where(Teacher.id == id)
    #         .values(**kwargs)
    #         .returning(Teacher)
    #     )
    #     res = await self.db_session.execute(query)
    #     updated_teacher = res.scalar()
    #     if updated_teacher:
    #         logger.info(f"У учителя с id: {id} были успешно обновлены поля: {{{', '.join(kwargs.keys())}}}")
    #         return updated_teacher

    #     logger.warning(f"Не было найдено ни одного учителя с таким id: {id}")
    #     return None