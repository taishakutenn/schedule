"""
File for creating validation models
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date


class TunedModel(BaseModel):
    class Config:
        """
        Tells pydantic to convert even non dict obj to json.
        We'll get fed up with this class
        """
        orm_mode = True
        from_attributes = True


class QueryParams(TunedModel):
    """
    This is model for validate query params
    when we need to retrieve all data from the table
     """
    page: int = Field(default=0, ge=0)
    limit: int = Field(default=10, ge=1, le=100)


'''
========
Teachers
========
'''

class ShowTeacher(TunedModel):
    """Class for get teacher info"""
    id: int
    name: str
    surname: str
    fathername: str | None = None
    phone_number: str
    email: EmailStr | None = None
    salary_rate: float | None = None
    teacher_category: str | None = None


class CreateTeacher(TunedModel):
    name: str
    surname: str
    fathername: str | None = None
    phone_number: str
    email: EmailStr | None = None
    salary_rate: float | None = None
    teacher_category: str | None = None


class UpdateTeacher(TunedModel):
    teacher_id: int
    name: str | None = None
    surname: str | None = None
    fathername: str | None = None
    phone_number: str | None = None
    email: EmailStr | None = None
    salary_rate: float | None = None
    teacher_category: str | None = None


class ShowTeacherWithHATEOAS(TunedModel):
    teacher: ShowTeacher
    links: dict[str, str] = {}


class ShowTeacherListWithHATEOAS(TunedModel):
    teachers: List[ShowTeacherWithHATEOAS]
    links: dict[str, str] = {}


'''
========
Building
========
'''

class ShowBuilding(TunedModel):
    """Class for get building info"""
    building_number: int
    city: str
    building_address: str


class CreateBuilding(TunedModel):
    building_number: int
    city: str = "Орск"
    building_address: str


class UpdateBuilding(TunedModel):
    building_number: int
    new_building_number: int | None = None
    city: str | None = None
    building_address: str | None = None


class ShowBuildingWithHATEOAS(TunedModel):
    building: ShowBuilding
    links: dict[str, str] = {}


class ShowBuildingListWithHATEOAS(TunedModel):
    buildings: List[ShowBuildingWithHATEOAS]
    links: dict[str, str] = {}


'''
========
Cabinet
========
'''

class ShowCabinet(TunedModel):
    """Class for get cabinet info"""
    cabinet_number: int
    building_number: int
    capacity: int | None = None
    cabinet_state: str | None = None


class CreateCabinet(TunedModel):
    cabinet_number: int
    building_number: int
    capacity: int | None = None
    cabinet_state: str | None = None


class UpdateCabinet(TunedModel):
    cabinet_number: int
    building_number: int
    new_cabinet_number: int | None = None
    new_building_number: int | None = None
    capacity: int | None = None
    cabinet_state: str | None = None


class ShowCabinetWithHATEOAS(TunedModel):
    cabinet: ShowCabinet
    links: dict[str, str] = {}


class ShowCabinetListWithHATEOAS(TunedModel):
    cabinets: List[ShowCabinetWithHATEOAS]
    links: dict[str, str] = {}


'''
========
Speciality
========
'''

class ShowSpeciality(TunedModel):
    """Class for get speciality info"""
    speciality_code: str


class CreateSpeciality(TunedModel):
    speciality_code: str


class UpdateSpeciality(TunedModel):
    speciality_code: str
    new_speciality_code: str | None = None


class ShowSpecialityWithHATEOAS(TunedModel):
    speciality: ShowSpeciality
    links: dict[str, str] = {}


class ShowSpecialityListWithHATEOAS(TunedModel):
    specialities: List[ShowSpecialityWithHATEOAS]
    links: dict[str, str] = {}


'''
========
Group
========
'''

class ShowGroup(TunedModel):
    """Class for get group info"""
    group_name: str
    speciality_code: str | None = None
    quantity_students: int | None = None
    group_advisor_id: int | None = None


class CreateGroup(TunedModel):
    group_name: str
    speciality_code: str | None = None
    quantity_students: int | None = None
    group_advisor_id: int | None = None


class UpdateGroup(TunedModel):
    group_name: str
    new_group_name: str | None = None
    speciality_code: str | None = None
    quantity_students: int | None = None
    group_advisor_id: int | None = None


class ShowGroupWithHATEOAS(TunedModel):
    group: ShowGroup
    links: dict[str, str] = {}


class ShowGroupListWithHATEOAS(TunedModel):
    groups: List[ShowGroupWithHATEOAS]
    links: dict[str, str] = {}


'''
==========
Curriculum
==========
''' 


class ShowCurriculum(TunedModel):
    """Class for get curriculum info"""
    semester_number: int
    group_name: str
    subject_code: str
    lectures_hours: int | None = None
    laboratory_hours: int | None = None
    practical_hours: int | None = None


class CreateCurriculum(TunedModel):
    semester_number: int
    group_name: str
    subject_code: str
    lectures_hours: int | None = None
    laboratory_hours: int | None = None
    practical_hours: int | None = None


class UpdateCurriculum(TunedModel):
    semester_number: int
    group_name: str
    subject_code: str
    new_semester_number: int | None = None
    new_group_name: str | None = None
    new_subject_code: str | None = None
    lectures_hours: int | None = None
    laboratory_hours: int | None = None
    practical_hours: int | None = None


class ShowCurriculumWithHATEOAS(TunedModel):
    curriculum: ShowCurriculum
    links: dict[str, str] = {}


class ShowCurriculumListWithHATEOAS(TunedModel):
    curriculums: List[ShowCurriculumWithHATEOAS]
    links: dict[str, str] = {}



'''
=======
Subject
=======
''' 


class ShowSubject(TunedModel):
    """Class for get subject info"""
    subject_code: str
    name: str | None = None


class CreateSubject(TunedModel):
    subject_code: str
    name: str | None = None


class UpdateSubject(TunedModel):
    subject_code: str
    new_subject_code: str | None = None 
    name: str | None = None


class ShowSubjectWithHATEOAS(TunedModel):
    subject: ShowSubject
    links: dict[str, str] = {}


class ShowSubjectListWithHATEOAS(TunedModel):
    subjects: List[ShowSubjectWithHATEOAS]
    links: dict[str, str] = {}


'''
=================
EmploymentTeacher
=================
''' 


class ShowEmployment(TunedModel):
    """Class for get subject info"""
    date_start_period: date
    date_end_period: date
    teacher_id: int
    monday: str | None = None
    tuesday: str | None = None
    wednesday: str | None = None
    thursday: str | None = None
    friday: str | None = None
    saturday: str | None = None


class CreateEmployment(TunedModel):
    date_start_period: date
    date_end_period: date
    teacher_id: int
    monday: str | None = None
    tuesday: str | None = None
    wednesday: str | None = None
    thursday: str | None = None
    friday: str | None = None
    saturday: str | None = None


class UpdateEmployment(TunedModel):
    date_start_period: date
    date_end_period: date
    teacher_id: int
    new_date_start_period: date | None = None
    new_date_end_period: date | None = None
    new_teacher_id: int | None = None
    monday: str | None = None
    tuesday: str | None = None
    wednesday: str | None = None
    thursday: str | None = None
    friday: str | None = None
    saturday: str | None = None


class ShowEmploymentWithHATEOAS(TunedModel):
    employment: ShowEmployment
    links: dict[str, str] = {}


class ShowEmploymentListWithHATEOAS(TunedModel):
    employments: List[ShowEmploymentWithHATEOAS]
    links: dict[str, str] = {}


'''
==============
TeacherRequest
==============
''' 


class ShowTeacherRequest(TunedModel):
    """Class for get subject info"""
    date_request: date
    teacher_id: int
    subject_code: str
    group_name: str
    lectures_hours: int
    laboratory_hours: int
    practice_hours: int


class CreateTeacherRequest(TunedModel):
    date_request: date
    teacher_id: int
    subject_code: str
    group_name: str
    lectures_hours: int
    laboratory_hours: int
    practice_hours: int


class UpdateTeacherRequest(TunedModel):
    date_request: date
    teacher_id: int
    subject_code: str
    group_name: str
    new_date_request: date | None = None
    new_teacher_id: int | None = None
    new_subject_code: str | None = None
    new_group_name: str | None = None
    lectures_hours: int | None = None
    laboratory_hours: int | None = None
    practice_hours: int | None = None


class ShowTeacherRequestWithHATEOAS(TunedModel):
    request: ShowTeacherRequest
    links: dict[str, str] = {}


class ShowTeacherRequestListWithHATEOAS(TunedModel):
    requests: List[ShowTeacherRequestWithHATEOAS]
    links: dict[str, str] = {}


'''
=======
Session
=======
'''


class ShowSession(TunedModel):
    session_number: int
    date: date
    group_name: str
    session_type: str
    subject_code: str | None = None
    teacher_id: int | None = None
    cabinet_number: int
    building_number: int


class CreateSession(TunedModel):
    session_number: int
    date: date
    group_name: str
    session_type: str
    subject_code: str | None = None
    teacher_id: int | None = None
    cabinet_number: int
    building_number: int


class UpdateSession(TunedModel):
    session_number: int
    session_date: date
    group_name: str
    new_session_number: int | None = None
    new_session_date: date | None = None
    new_group_name: str | None = None
    session_type: str | None = None
    subject_code: str | None = None
    teacher_id: int | None = None
    cabinet_number: int | None = None
    building_number: int | None = None


class ShowSessionWithHATEOAS(TunedModel):
    session: ShowSession
    links: dict[str, str] = {}


class ShowSessionListWithHATEOAS(TunedModel):
    sessions: List[ShowSessionWithHATEOAS]
    links: dict[str, str] = {}



'''
===============
TeacherCategory
===============
'''

class CreateTeacherCategory(BaseModel):
    teacher_category: str


class UpdateTeacherCategory(BaseModel):
    teacher_category: Optional[str] = None
    new_teacher_category: Optional[str] = None 


class ShowTeacherCategory(BaseModel):
    teacher_category: str


class ShowTeacherCategoryWithHATEOAS(BaseModel):
    category: ShowTeacherCategory
    links: dict[str, str]


class ShowTeacherCategoryListWithHATEOAS(BaseModel):
    categories: List[ShowTeacherCategoryWithHATEOAS]
    links: dict[str, str]


'''
========
SessionType
========
'''

class ShowSessionType(TunedModel):
    """Class for get session type info"""
    name: str


class CreateSessionType(TunedModel):
    name: str


class UpdateSessionType(TunedModel):
    current_name: str
    new_name: str


class ShowSessionTypeWithHATEOAS(TunedModel):
    session_type: ShowSessionType
    links: dict[str, str] = {}


class ShowSessionTypeListWithHATEOAS(TunedModel):
    session_types: List[ShowSessionTypeWithHATEOAS]
    links: dict[str, str] = {}


'''
========
Semester
========
'''

class ShowSemester(TunedModel):
    """Class for get semester info"""
    semester: int
    weeks: float
    practice_weeks: int
    plan_id: int


class CreateSemester(TunedModel):
    semester: int
    weeks: float
    practice_weeks: int
    plan_id: int


class UpdateSemester(TunedModel):
    semester: int
    plan_id: int
    new_semester: int | None = None
    new_plan_id: int | None = None
    weeks: float | None = None
    practice_weeks: int | None = None


class ShowSemesterWithHATEOAS(TunedModel):
    semester: ShowSemester
    links: dict[str, str] = {}


class ShowSemesterListWithHATEOAS(TunedModel):
    semesters: List[ShowSemesterWithHATEOAS]
    links: dict[str, str] = {}


'''
====
Plan
====
'''

class ShowPlan(TunedModel):
    """Class for get plan info"""
    id: int
    year: int
    speciality_code: str


class CreatePlan(TunedModel):
    year: int
    speciality_code: str


class UpdatePlan(TunedModel):
    plan_id: int
    year: int | None = None
    speciality_code: str | None = None


class ShowPlanWithHATEOAS(TunedModel):
    plan: ShowPlan
    links: dict[str, str] = {}


class ShowPlanListWithHATEOAS(TunedModel):
    plans: List[ShowPlanWithHATEOAS]
    links: dict[str, str] = {}


'''
========
Chapter
========
'''

class ShowChapter(TunedModel):
    """Class for get chapter info"""
    id: int
    code: str
    name: str
    plan_id: int


class CreateChapter(TunedModel):
    code: str
    name: str
    plan_id: int


class UpdateChapter(TunedModel):
    chapter_id: int
    code: str | None = None
    name: str | None = None
    plan_id: int | None = None


class ShowChapterWithHATEOAS(TunedModel):
    chapter: ShowChapter
    links: dict[str, str] = {}


class ShowChapterListWithHATEOAS(TunedModel):
    chapters: List[ShowChapterWithHATEOAS]
    links: dict[str, str] = {}


'''
========
Cycle
========
'''

class ShowCycle(TunedModel):
    """Class for get cycle info"""
    id: int
    contains_modules: bool
    code: str
    name: str
    chapter_in_plan_id: int


class CreateCycle(TunedModel):
    contains_modules: bool
    code: str
    name: str
    chapter_in_plan_id: int


class UpdateCycle(TunedModel):
    cycle_id: int
    contains_modules: bool | None = None
    code: str | None = None
    name: str | None = None
    chapter_in_plan_id: int | None = None


class ShowCycleWithHATEOAS(TunedModel):
    cycle: ShowCycle
    links: dict[str, str] = {}


class ShowCycleListWithHATEOAS(TunedModel):
    cycles: List[ShowCycleWithHATEOAS]
    links: dict[str, str] = {}


'''
========
Module
========
'''

class ShowModule(TunedModel):
    """Class for get module info"""
    id: int
    name: str
    code: str
    cycle_in_chapter_id: int


class CreateModule(TunedModel):
    name: str
    code: str
    cycle_in_chapter_id: int


class UpdateModule(TunedModel):
    module_id: int
    name: str | None = None
    code: str | None = None
    cycle_in_chapter_id: int | None = None


class ShowModuleWithHATEOAS(TunedModel):
    module: ShowModule
    links: dict[str, str] = {}


class ShowModuleListWithHATEOAS(TunedModel):
    modules: List[ShowModuleWithHATEOAS]
    links: dict[str, str] = {}


'''
===============
SubjectsInCycle
===============
'''

class ShowSubjectsInCycle(TunedModel):
    """Class for get subject in cycle info"""
    id: int
    code: str
    title: str
    module_in_cycle_id: int | None = None
    cycle_in_chapter_id: int


class CreateSubjectsInCycle(TunedModel):
    code: str
    title: str
    module_in_cycle_id: int | None = None
    cycle_in_chapter_id: int


class UpdateSubjectsInCycle(TunedModel):
    subject_in_cycle_id: int
    code: str | None = None
    title: str | None = None
    module_in_cycle_id: int | None = None
    cycle_in_chapter_id: int | None = None


class ShowSubjectsInCycleWithHATEOAS(TunedModel):
    subject_in_cycle: ShowSubjectsInCycle
    links: dict[str, str] = {}


class ShowSubjectsInCycleListWithHATEOAS(TunedModel):
    subjects_in_cycles: List[ShowSubjectsInCycleWithHATEOAS]
    links: dict[str, str] = {}


'''
========
SubjectsInCycleHours
========
'''

class ShowSubjectsInCycleHours(TunedModel):
    """Class for get subject in cycle hours info"""
    id: int
    semester: int
    self_study_hours: int
    lectures_hours: int
    laboratory_hours: int
    practical_hours: int
    course_project_hours: int
    consultation_hours: int
    intermediate_assessment_hours: int
    subject_in_cycle_id: int


class CreateSubjectsInCycleHours(TunedModel):
    semester: int
    self_study_hours: int
    lectures_hours: int
    laboratory_hours: int
    practical_hours: int
    course_project_hours: int
    consultation_hours: int
    intermediate_assessment_hours: int
    subject_in_cycle_id: int


class UpdateSubjectsInCycleHours(TunedModel):
    hours_id: int
    semester: int | None = None
    self_study_hours: int | None = None
    lectures_hours: int | None = None
    laboratory_hours: int | None = None
    practical_hours: int | None = None
    course_project_hours: int | None = None
    consultation_hours: int | None = None
    intermediate_assessment_hours: int | None = None
    subject_in_cycle_id: int | None = None


class ShowSubjectsInCycleHoursWithHATEOAS(TunedModel):
    subject_in_cycle_hours: ShowSubjectsInCycleHours
    links: dict[str, str] = {}


class ShowSubjectsInCycleHoursListWithHATEOAS(TunedModel):
    subjects_in_cycle_hours: List[ShowSubjectsInCycleHoursWithHATEOAS]
    links: dict[str, str] = {}


'''
========
Certification
========
'''

class ShowCertification(TunedModel):
    """Class for get certification info"""
    id: int
    credit: bool
    differentiated_credit: bool
    course_project: bool
    course_work: bool
    control_work: bool
    other_form: bool


class CreateCertification(TunedModel):
    id: int
    credit: bool = False
    differentiated_credit: bool = False
    course_project: bool = False
    course_work: bool = False
    control_work: bool = False
    other_form: bool = False


class UpdateCertification(TunedModel):
    certification_id: int
    credit: bool | None = None
    differentiated_credit: bool | None = None
    course_project: bool | None = None
    course_work: bool | None = None
    control_work: bool | None = None
    other_form: bool | None = None


class ShowCertificationWithHATEOAS(TunedModel):
    certification: ShowCertification
    links: dict[str, str] = {}


class ShowCertificationListWithHATEOAS(TunedModel):
    certifications: List[ShowCertificationWithHATEOAS]
    links: dict[str, str] = {}


'''
========
TeacherInPlan
========
'''

class ShowTeacherInPlan(TunedModel):
    """Class for get teacher in plan info"""
    id: int
    subject_in_cycle_hours_id: int
    teacher_id: int
    group_name: str
    session_type: str


class CreateTeacherInPlan(TunedModel):
    subject_in_cycle_hours_id: int
    teacher_id: int
    group_name: str
    session_type: str


class UpdateTeacherInPlan(TunedModel):
    teacher_in_plan_id: int
    subject_in_cycle_hours_id: int | None = None
    teacher_id: int | None = None
    group_name: str | None = None
    session_type: str | None = None


class ShowTeacherInPlanWithHATEOAS(TunedModel):
    teacher_in_plan: ShowTeacherInPlan
    links: dict[str, str] = {}


class ShowTeacherInPlanListWithHATEOAS(TunedModel):
    teachers_in_plans: List[ShowTeacherInPlanWithHATEOAS]
    links: dict[str, str] = {}