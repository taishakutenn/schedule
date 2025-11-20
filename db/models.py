'''File for database models'''

from sqlalchemy import (Column, String, Boolean, Integer, Numeric, ForeignKey, Date, ForeignKeyConstraint,
                        and_, Table, Double)
from sqlalchemy.orm import relationship, DeclarativeBase, foreign


class Base(DeclarativeBase):
    """
    We create a base class needed to create all other orm classes
    Since it is inherited from DeclarativeBase,
    we don't need to write anything inside it, everything is already there
    When creating all other models, you need to inherit from this class
    """
    pass


class Group(Base):
    """
    Represents a group of students in the database

    Fields:
        group_name (str): The unique name of the group (primary key)
        speciality_code (str): The code of the specialty associated with the group
        quantity_students (int): The number of students in the group
        group_advisor_id (int): Foreign key linking to the teacher who advises the group

    Relations:
        advisor (Teacher): Relationship to access the advisor (Teacher) of the group
        speciality (Speciality): Relationship to access the speciality of the group
        sessions (Session): Relationship to access the sessions associated with the group
        requests (TeacherRequest): Relationship to access the teacher requests for sessions associated with the group
        streams (Stream): Relationship to access the stream with the group
        teachers_in_plans (TeacherInPlan): Relationship to access the teacher in_plans of the group
    """
    __tablename__ = "groups"

    group_name = Column(String, primary_key=True, unique=True, nullable=False)
    quantity_students = Column(Integer, nullable=True)

    # Foreign keys
    group_advisor_id = Column(Integer, ForeignKey("teachers.id", onupdate="CASCADE", ondelete="SET NULL"),
                              nullable=True)
    speciality_code = Column(String,
                             ForeignKey("specialties.speciality_code", onupdate="CASCADE", ondelete="SET NULL"),
                             nullable=True)

    # Relationships
    advisor = relationship("Teacher", back_populates="advisory_group", uselist=False)  # uselist for one to one
    speciality = relationship("Speciality", back_populates="groups")
    # requests = relationship("TeacherRequest", back_populates="group")
    streams = relationship("Stream", back_populates="group")
    teachers_in_plans = relationship("TeacherInPlan", back_populates="group")


class Speciality(Base):
    """
    Represents the received specialties in the database

    Fields:
        speciality_code (str): The unique name of the speciality (primary key)

    Relations:
        groups (Group): Relationship to access the group of the speciality
        plans (Plan): Relationship to access the educational plans of the speciality
    """
    __tablename__ = "specialties"

    speciality_code = Column(String, primary_key=True, unique=True, nullable=False)

    # Relationships
    groups = relationship("Group", back_populates="speciality")
    plans = relationship("Plan", back_populates="speciality")


class TeacherCategory(Base):
    """
    Represents teacher categories (e.g. 'Преподаватель высшей категории')

    Fields:
        category (str):  The unique name of the category
        teachers: Relationship to access the teachers of the current category
    """
    __tablename__ = "teacher_categories"

    teacher_category = Column(String, primary_key=True, unique=True, nullable=False)

    # Relationships
    teachers = relationship("Teacher", back_populates="category")


class Teacher(Base):
    """
    Represent the teacher in the database

    Fields:
        id (int): The unique number of the teacher (primary key)
        name (str): Just name of the teacher
        surname (str): Just surname of the teacher
        fathername (str): Just father(mother)name of the teacher (optional)
        phone_number (str): Phone number to contact the teacher
        email (str): Work email address to contact the teacher (optional)
        salary_rate (Numeric): Hourly rate of a teacher

    Relations:
        advisory_group (Group): Relationship to access the group in which the teacher is an advisory
        employments (EmploymentTeacher): Relationship to access the employments associated with the teacher
        requests (TeacherRequest): Relationship to access the teacher requests for sessions associated with the teacher
        category (TeacherCategory): Relationship to access the category associated with the current teacher
        teachers_in_plans (TeacherInPlan): Relationship to access the teachers in plans associated with the current teacher
        buildings_work (TeacherBuilding): Relationship to access the all buildings work associated with the current teacher
    """
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    fathername = Column(String, nullable=True)
    phone_number = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=True)
    # salary_rate = Column(Numeric, nullable=True)

    # Foreign keys
    teacher_category = Column(String,
                              ForeignKey("teacher_categories.teacher_category", onupdate="CASCADE",
                                         ondelete="SET NULL"),
                              nullable=True)

    # Relationships
    advisory_group = relationship("Group", back_populates="advisor")
    # employments = relationship("EmploymentTeacher", back_populates="teacher")
    # requests = relationship("TeacherRequest", back_populates="teacher")
    category = relationship("TeacherCategory", back_populates="teachers")
    teachers_in_plans = relationship("TeacherInPlan", back_populates="teacher")
    buildings_work = relationship("TeacherBuilding", back_populates="teacher")


# class Subject(Base):
#     """
#     Represent the subjects studied in the database

#     Fields:
#         subject_code: Stores the subject code in the general structure of the college
#         name: Human-readable name of the item
#         sessions: Relationship to access the sessions associated with the subject
#         requests: Relationship to access the teacher requests for sessions associated with the subject
#         streams: Relationship to access the stream with the subject
#     """
#     __tablename__ = "subjects"

#     subject_code = Column(String, primary_key=True, unique=True, nullable=False)
#     name = Column(String, nullable=True)

#     # Relationships
#     sessions = relationship("Session", back_populates="subject")
#     requests = relationship("TeacherRequest", back_populates="subject")
#     streams = relationship("Stream", back_populates="subject")


class Cabinet(Base):
    """
    Represents a cabinet in the database

    Fields:
        cabinet_number (int): The unique number of the cabinets in the one building (primary key)
        capacity (int): The meaning of how many people can fit in one cabinet
        cabinet_state (str): The current state of the cabinet (e.g., "Equipped with PC", "Repair")
        building_number (int): This is the foreign key of the building where the cabinet is located

    Relations:
        building (Building): Relationship for access building where the cabinet is located
        sessions (Session): Relationship to access the sessions associated with the cabinet
    """
    __tablename__ = "cabinets"

    cabinet_number = Column(Integer, primary_key=True, nullable=False)
    capacity = Column(Integer, nullable=True)
    cabinet_state = Column(String, nullable=True)

    # Foreign keys
    building_number = Column(Integer, ForeignKey("buildings.building_number", onupdate="CASCADE", ondelete="SET NULL"),
                             primary_key=True)

    # Relationships
    building = relationship("Building", back_populates="cabinets")
    sessions = relationship(
        "Session",
        primaryjoin="and_(Cabinet.cabinet_number == Session.cabinet_number, "
                    "Cabinet.building_number == Session.building_number)",
        back_populates="cabinet"
    )


class Building(Base):
    """
    Represents a building in the database

    Fields:
        building_number (int): The unique number of the building (primary_key)
        city (str): The city where the building is located
        building_address (str): The building address

    Relations:
        cabinets (Cabinet): Relationship to access all cabinets associated with this building
        teachers_work (TeacherBuilding): Relationship to access the building and all teachers teaching in that building
    """
    __tablename__ = "buildings"

    building_number = Column(Integer, primary_key=True, nullable=False)
    city = Column(String, nullable=False, default="Орск")
    building_address = Column(String, nullable=False)

    # Relationships
    cabinets = relationship("Cabinet", back_populates="building")
    teachers_work = relationship("TeacherBuilding", back_populates="building")


class TeacherBuilding(Base):
    """
    Represent the buildings in which the teacher works

    Fields:
        id (int): The unique number of the teacher-group relation (primary key)

    Relations:
        teacher (Teacher): Relationship to with teachers who teach
        building (Building): Relationship to the buildings in which teachers teach
    """
    __tablename__ = "teachers_buildings"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    building_number = Column(Integer, ForeignKey("buildings.building_number", ondelete="CASCADE", onupdate="CASCADE"),
                             nullable=False)

    # Relations
    teacher = relationship("Teacher", back_populates="buildings_work")
    building = relationship("Building", back_populates="teachers_work")


class SessionType(Base):
    """
    Represents are anybody type session

    Fields:
        name (str): А name of the type session, primary key

    Relations:
        sessions (Session): Relationship to access the all sessions associated with the type
    """
    __tablename__ = "session_types"

    name = Column(String, primary_key=True)

    # Relationships
    sessions = relationship("Session", back_populates="type")


class Session(Base):
    """
    Represents a one learn session in the database

    Fields:
        session_number (int): This is what number the session is on that day (primary key)
        date (date): This is the date of the session (primary key)
        session_type (int): This is the type of the session (e.g. "lecture" or "laboratory")
        group_name (int): Foreign key field for linking to the teacher_in table,
            which has information about: teacher, group, subject (primary key)
        cabinet_number (int): Foreign key field for linking to the cabinets table
        building_number (int): Second foreign key field for linking to the building number

    Relations:
        plan (Plan): Relationship to access the teacher in plan associated with this session
        type (SessionType): Relationship to access this session associated with her type
        cabinet (Cabinet): Relationship to access the cabinet associated with this session
    """
    __tablename__ = "sessions"

    session_number = Column(Integer, primary_key=True, nullable=False)
    date = Column(Date, primary_key=True, nullable=False)

    # Foreign keys
    teacher_in_plan = Column(Integer, ForeignKey("teachers_in_plans.id", onupdate="CASCADE", ondelete="CASCADE"))
    session_type = Column(String, ForeignKey("session_types.name", onupdate="CASCADE", ondelete="CASCADE"))
    cabinet_number = Column(Integer, nullable=True)
    building_number = Column(Integer, nullable=True)

    # For a composite primary key
    __table_args__ = (
        ForeignKeyConstraint(
            ['cabinet_number', 'building_number'],
            ['cabinets.cabinet_number', 'cabinets.building_number'],
            onupdate="CASCADE", ondelete="SET NULL"
        ),
    )

    # Relationships
    plan = relationship("TeacherInPlan", back_populates="sessions")
    type = relationship("SessionType", back_populates="sessions")
    cabinet = relationship(
        "Cabinet",
        primaryjoin="and_(Session.cabinet_number == Cabinet.cabinet_number, "
                    "Session.building_number == Cabinet.building_number)",
        back_populates="sessions"
    )


# class EmploymentTeacher(Base):
#     """
#     Represents an employment teacher in the database
#
#     Fields:
#         date_start_period: This field stores the beginning of the period in which the teacher indicates his employment (Primary Key)
#         date_end_period: This field stores the ending of the period in which the teacher indicates his employment (Primary Key)
#         monday, tuesday, wednesday, thursday, friday, saturday: All fields with names of working days of the week -
#             store the value of how much the teacher can work on this day.
#             Also, it can take the value null - in this case it will be considered that in this period,
#             on this day, the teacher will not be able to work
#         teacher_id: Foreign key field for linking to the teachers table
#         teacher: Relationship to access the teacher associated with this employment teacher
#     """
#     __tablename__ = "employment_teachers"
#
#     date_start_period = Column(Date, primary_key=True, nullable=False)
#     date_end_period = Column(Date, primary_key=True, nullable=False)
#     monday = Column(String, nullable=True, default="8:30")
#     tuesday = Column(String, nullable=True, default="8:30")
#     wednesday = Column(String, nullable=True, default="8:30")
#     thursday = Column(String, nullable=True, default="8:30")
#     friday = Column(String, nullable=True, default="8:30")
#     saturday = Column(String, nullable=True, default="8:30")
#
#     # Foreign keys
#     teacher_id = Column(Integer, ForeignKey("teachers.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
#
#     # Relationships
#     teacher = relationship("Teacher", back_populates="employments")
#
#
# class TeacherRequest(Base):
#     """
#     Represents a teacher request in the database
#
#     Fields:
#         date_request: This field stores the day that the teacher selects and the whole week will be counted from it.
#             Thus, indicating the beginning of the week - the whole week is indicated
#             and the teacher's request goes for the whole week (Primary Key)
#         lectures_hours: Field storing the number of hours in request for lectures
#         laboratory_hours: Field storing the number of hours in request  for laboratories
#         practice_hours: Field storing the number of hours in request  for practices
#         teacher_id: Foreign key field for linking to the teachers table
#         subject_code: Foreign key field for linking to the subjects table
#         group_name: Foreign key field for linking to the groups table
#         teacher: Relationship to access the teacher associated with this request
#         subject: Relationship to access the subject for which it was created session
#         group: Relationship to access the group for which it was created session
#     """
#     __tablename__ = "teacher_requests"
#
#     date_request = Column(Date, primary_key=True, nullable=False)
#     lectures_hours = Column(Integer, nullable=False, default=0)
#     laboratory_hours = Column(Integer, nullable=False, default=0)
#     practice_hours = Column(Integer, nullable=False, default=0)
#
#     # Foreign keys
#     teacher_id = Column(Integer, ForeignKey("teachers.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
#     subject_code = Column(String, ForeignKey("subjects.subject_code", onupdate="CASCADE", ondelete="SET NULL"),
#                           primary_key=True)
#     group_name = Column(String, ForeignKey("groups.group_name", onupdate="CASCADE", ondelete="SET NULL"),
#                         primary_key=True)
#
#     # Relationships
#     teacher = relationship("Teacher", back_populates="requests")
#     subject = relationship("Subject", back_populates="requests")
#     group = relationship("Group", back_populates="requests")


class Semester(Base):
    """
    A table that stores information about how many weeks there are in a semester

    Fields:
        semester (int): The number of the semester (primary key)
        weeks (float): Total number of weeks in the semester
        practice_weeks (int): Number of weeks allocated for practice
        plan_id (int): Foreign key linking to the academic plan (primary key)

    Relations:
        plan (Plan): Relationship to access the academic plan this semester belongs to
    """
    __tablename__ = "semesters"

    semester = Column(Integer, primary_key=True)
    weeks = Column(Double, nullable=False)
    practice_weeks = Column(Integer, nullable=False)

    # Foreign keys
    plan_id = Column(Integer, ForeignKey("plans.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)

    # Relationships
    plan = relationship("Plan", back_populates="semesters")


class Plan(Base):
    """
    Represents an academic plan in the database

    Fields:
        id (int): Unique identifier of the plan (primary key)
        year (int): The year the plan is intended for
        speciality_code (str): Foreign key linking to the specialty this plan belongs to

    Relations:
        speciality (Speciality): Relationship to access the specialty associated with this plan
        chapters (Chapter): Relationship to access all chapters in this plan
        semesters (Semester): Relationship to access all semesters defined in this plan
    """
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)

    # Foreign keys
    speciality_code = Column(String,
                             ForeignKey("specialties.speciality_code", onupdate="CASCADE", ondelete="SET NULL"),
                             nullable=False)

    # Relationships
    speciality = relationship("Speciality", back_populates="plans")
    chapters = relationship("Chapter", back_populates="plan")
    semesters = relationship("Semester", back_populates="plan")


class Chapter(Base):
    """
    Represents a chapter within an academic plan

    Fields:
        id (int): Unique identifier of the chapter (primary key)
        code (str): Code of the chapter
        name (str): Name of the chapter
        plan_id (int): Foreign key linking to the academic plan

    Relations:
        plan (Plan): Relationship to access the academic plan this chapter belongs to
        cycles (List[Cycle]): Relationship to access all cycles within this chapter
    """
    __tablename__ = "chapter_in_plan"

    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)

    # Foreign keys
    plan_id = Column(Integer, ForeignKey("plans.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)

    # Relationships
    plan = relationship("Plan", back_populates="chapters")
    cycles = relationship("Cycle", back_populates="chapter")


class Cycle(Base):
    """
    Represents a cycle within a chapter of an academic plan

    Fields:
        id (int): Unique identifier of the cycle (primary key)
        contains_modules (bool): Indicates whether this cycle contains modules
        code (str): Code of the cycle
        name (str): Name of the cycle 
        chapter_in_plan_id (int): Foreign key linking to the chapter

    Relations:
        chapter (Chapter): Relationship to access the chapter this cycle belongs to
        modules (List[Module]): Relationship to access all modules in this cycle
        subjects_in_cycle (List[SubjectsInCycle]): Relationship to access all subjects assigned to this cycle
    """
    __tablename__ = "cycle_in_chapter"

    id = Column(Integer, primary_key=True)
    contains_modules = Column(Boolean, nullable=False, default=False)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)

    # Foreign keys
    chapter_in_plan_id = Column(Integer,
                                ForeignKey("chapter_in_plan.id", onupdate="CASCADE", ondelete="CASCADE"),
                                nullable=False)

    # Relationships
    chapter = relationship("Chapter", back_populates="cycles")
    modules = relationship("Module", back_populates="cycle")
    subjects_in_cycle = relationship("SubjectsInCycle", back_populates="cycle")


class Module(Base):
    """
    Represents a module within a cycle

    Fields:
        id (int): Unique identifier of the module (primary key)
        name (str): Name of the module
        code (str): Code of the module
        cycle_in_chapter_id (int): Foreign key linking to the cycle

    Relations:
        cycle (Cycle): Relationship to access the cycle this module belongs to
        subjects (SubjectsInCycle): Relationship to access all subjects assigned to this module
    """
    __tablename__ = "module_in_cycle"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False)

    # Foreign keys
    cycle_in_chapter_id = Column(Integer,
                                 ForeignKey("cycle_in_chapter.id", onupdate="CASCADE", ondelete="CASCADE"))

    # Relationships
    cycle = relationship("Cycle", back_populates="modules")
    subjects = relationship("SubjectsInCycle", back_populates="module")


class SubjectsInCycle(Base):
    """
    Represents a subject assigned to a cycle (and optionally a module)

    Fields:
        id (int): Unique identifier of the subject assignment (primary key)
        code (str): Code of the subject
        title (str): Title of the subject
        module_in_cycle_id (int): Foreign key linking to the module (nullable)
        cycle_in_chapter_id (int): Foreign key linking to the cycle

    Relations:
        module (Module): Relationship to access the module this subject belongs to (if any)
        cycle (Cycle): Relationship to access the cycle this subject belongs to
        hours (SubjectsInCycleHours): Relationship to access hour distributions for this subject
        streams (Stream): Relationship to access the streams this subject belongs to
    """
    __tablename__ = "subjects_in_cycle"

    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False)
    title = Column(String, nullable=False)

    # Foreign keys
    module_in_cycle_id = Column(Integer,
                                ForeignKey("module_in_cycle.id", onupdate="CASCADE", ondelete="CASCADE"),
                                nullable=True)
    cycle_in_chapter_id = Column(Integer,
                                 ForeignKey("cycle_in_chapter.id", onupdate="CASCADE", ondelete="CASCADE"),
                                 nullable=True)

    # Relationships
    module = relationship("Module", back_populates="subjects")
    cycle = relationship("Cycle", back_populates="subjects_in_cycle")
    hours = relationship("SubjectsInCycleHours", back_populates="subjects_in_cycle")
    streams = relationship("Stream", back_populates="subject")


class SubjectsInCycleHours(Base):
    """
    Represents the distribution of hours for a subject in a specific semester

    Fields:
        id (int): Unique identifier of the hour record (primary key)
        semester (int): Semester number for which the hours are defined
        self_study_hours (int): Hours for self-study
        lectures_hours (int): Lecture hours
        laboratory_hours (int): Laboratory work hours
        practical_hours (int): Practical session hours
        course_project_hours (int): Hours for course project
        consultation_hours (int): Consultation hours
        intermediate_assessment_hours (int): Hours for intermediate assessment
        subject_in_cycle_id (int): Foreign key linking to the subject assignment

    Relations:
        subjects_in_cycle (SubjectsInCycle): Relationship to access the subject this hour record belongs to
        teachers_in_plans (TeacherInPlan): Relationship to access the teacher in plan this hour record belongs to
        certifications (Certification): Relationship to access the subject this hour record belongs to
    """
    __tablename__ = "subjects_in_cycle_hours"

    id = Column(Integer, primary_key=True)
    semester = Column(Integer, nullable=False)
    self_study_hours = Column(Integer, nullable=False)
    lectures_hours = Column(Integer, nullable=False)
    laboratory_hours = Column(Integer, nullable=False)
    practical_hours = Column(Integer, nullable=False)
    course_project_hours = Column(Integer, nullable=False)
    consultation_hours = Column(Integer, nullable=False)
    intermediate_assessment_hours = Column(Integer, nullable=False)

    # Foreign keys
    subject_in_cycle_id = Column(Integer,
                                 ForeignKey("subjects_in_cycle.id", onupdate="CASCADE", ondelete="CASCADE"),
                                 nullable=False)

    # Relationships
    subjects_in_cycle = relationship("SubjectsInCycle", back_populates="hours")
    teachers_in_plans = relationship("TeacherInPlan", back_populates="subjects_hours")
    certifications = relationship("Certification", back_populates="subjects_in_cycle_hours")


class Certification(Base):
    """
    Displays whether anything is due in each semester of each plan for each subject

    Fields:
        id (int): Foreign key id to a specific semester, specific plan, specific subject (primary key)
        credit (bool): Form of credit (e.g., "exam", "pass")
        differentiated_credit (bool): Differentiated credit info
        course_project (bool): Requirement for course project
        course_work (bool): Requirement for course work
        control_work (bool): Requirement for control work
        other_form (bool): Other assessment forms

    Relations:
        subjects_in_cycle_hours (SubjectsInCycleHours): Relationship to access the subject this hour record belongs to
    """
    __tablename__ = "certifications"

    credit = Column(Boolean, nullable=False, default=False)
    differentiated_credit = Column(Boolean, nullable=False, default=False)
    course_project = Column(Boolean, nullable=False, default=False)
    course_work = Column(Boolean, nullable=False, default=False)
    control_work = Column(Boolean, nullable=False, default=False)
    other_form = Column(Boolean, nullable=False, default=False)

    # Foreign keys
    id = Column(Integer, ForeignKey("subjects_in_cycle_hours.id", ondelete="CASCADE", onupdate="CASCADE"),
                primary_key=True)

    # Relationships
    subjects_in_cycle_hours = relationship("SubjectsInCycleHours", back_populates="certifications")


class TeacherInPlan(Base):
    """
    Represents an assignment of a teacher to a subject for a specific group and session type

    Fields:
        id (int): Unique identifier of the assignment (primary key)
        subject_in_cycle_hours_id (int): Foreign key linking to the subject hour record
        teacher_id (int): Foreign key linking to the teacher
        group_name (str): Foreign key linking to the student group
        session_type (str): Foreign key linking to the session type

    Relations:
        subjects_hours (SubjectsInCycleHours): Relationship to access the subject hour record this assignment is based on
        teacher (Teacher): Relationship to access the teacher assigned in this plan entry
        group (Group): Relationship to access the student group this assignment applies to
        sessions (Session): Relationship to access all sessions created from this assignment
    """
    __tablename__ = "teachers_in_plans"

    id = Column(Integer, primary_key=True)

    # Foreign key
    subject_in_cycle_hours_id = Column(Integer,
                                       ForeignKey("subjects_in_cycle_hours.id", onupdate="CASCADE", ondelete="CASCADE"))
    teacher_id = Column(Integer, ForeignKey("teachers.id", onupdate="CASCADE", ondelete="CASCADE"))
    group_name = Column(String, ForeignKey("groups.group_name", onupdate="CASCADE", ondelete="CASCADE"))
    session_type = Column(String, ForeignKey("session_types.name", onupdate="CASCADE", ondelete="CASCADE"))

    # Relationships
    subjects_hours = relationship("SubjectsInCycleHours", back_populates="teachers_in_plans")
    teacher = relationship("Teacher", back_populates="teachers_in_plans")
    group = relationship("Group", back_populates="teachers_in_plans")
    sessions = relationship("Session", back_populates="plan")


class Stream(Base):
    """
    Represents a stream in the database

    Fields:
        stream_id (int): Identifier of the stream (primary key, not auto-incremented)
        group_name (str): Foreign key linking to the student group (primary key)
        subject_id (int): Foreign key linking to the subject (primary key)

    Relations:
        group (Group): Relationship to access the group in this stream
        subject (Subject): Relationship to access the subject in this stream
    """
    __tablename__ = "streams"

    stream_id = Column(Integer, primary_key=True, autoincrement=False)

    # Foreign keys
    group_name = Column(String, ForeignKey("groups.group_name", onupdate="CASCADE", ondelete="CASCADE"),
                        primary_key=True)
    subject_id = Column(Integer, ForeignKey("subjects_in_cycle.id", onupdate="CASCADE", ondelete="CASCADE"),
                        primary_key=True)

    # Relationships
    group = relationship("Group", back_populates="streams")
    subject = relationship("SubjectsInCycle", back_populates="streams")


class Token(Base):
    """
    Represents a token for using api
    More information about the tokens read in the habr: https://habr.com/ru/articles/533868/

    Fields:
        token_id: Just primary key in the table what not to do 3 primary key
        access_token: Token that will store user data, site signature. Lives for a very short period
        refresh_token: A token that will automatically allow you to get a new pair of access_token and refresh_token tokens
    """
    __tablename__ = "tokens"

    token_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)

    def generate_access_token(self):
        """Function for generating the access_token"""
        pass

    def generate_refresh_token(self):
        """Function for generating the refresh_token"""
        pass

    def set_token(self, access_token, refresh_token):
        """Function which set the tokens"""
        pass
