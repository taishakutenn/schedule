'''File for database models'''

from sqlalchemy import Column, String, Boolean, Integer, Numeric, ForeignKey, Date, ForeignKeyConstraint, and_, Table
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
        group_name: The unique name of the group (primary key)
        speciality_code: The code of the specialty associated with the group
        quantity_students: The number of students in the group
        group_advisor_id: Foreign key linking to the teacher who advises the group
        advisor: Relationship to access the advisor (Teacher) of the group
        speciality: Relationship to access the speciality of the group
        curriculums: Relationship to access the curriculum for this group
        sessions: Relationship to access the sessions associated with the group
        requests: Relationship to access the teacher requests for sessions associated with the group
    """
    __tablename__ = "groups"

    group_name = Column(String, primary_key=True, unique=True, nullable=False)
    quantity_students = Column(Integer, nullable=True)

    # Foreign keys
    group_advisor_id = Column(Integer, ForeignKey("teachers.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    speciality_code = Column(String, 
                            ForeignKey("specialties.speciality_code", onupdate="CASCADE", ondelete="SET NULL"), 
                            nullable=True)

    # Relationships
    advisor = relationship("Teacher", back_populates="advisory_group", uselist=False)  # uselist for one to one
    speciality = relationship("Speciality", back_populates="groups")
    curriculums = relationship("Curriculum", back_populates="group")
    sessions = relationship("Session", back_populates="group")
    requests = relationship("TeacherRequest", back_populates="group")


class Speciality(Base):
    """
    Represents the received specialties in the database

    Fields:
        speciality_code: The unique name of the speciality (primary key)
        groups: Relationship to access the group of the speciality
    """
    __tablename__ = "specialties"

    speciality_code = Column(String, primary_key=True, unique=True, nullable=False)

    # Relationships
    groups = relationship("Group", back_populates="speciality")


# Create many-to-many table for bind teachers and his subjects
teacher_subject = Table("teacher_subject", Base.metadata,
                        Column("teacher_id", Integer(), ForeignKey("teachers.id")),
                        Column("subject_code", String(), ForeignKey("subjects.subject_code"))
                        )


class Teacher(Base):
    """
    Represent the teacher in the database

    Fields:
        id: The unique number of the teacher (primary key)
        name: Just name of the teacher
        surname: Just surname of the teacher
        fathername: Just father(mother)name of the teacher (optional)
        phone_number: Phone number to contact the teacher
        email: Work email address to contact the teacher (optional)
        advisory_group: Relationship to access the group in which the teacher is an advisory
        sessions: Relationship to access the sessions associated with the teacher
        employments: Relationship to access the employments associated with the teacher
        requests: Relationship to access the teacher requests for sessions associated with the teacher
    """
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    fathername = Column(String, nullable=True)
    phone_number = Column(String, unique = True, nullable=False)
    email = Column(String, unique = True, nullable=True)

    # Relationships
    advisory_group = relationship("Group", back_populates="advisor")
    sessions = relationship("Session", back_populates="teacher")
    employments = relationship("EmploymentTeacher", back_populates="teacher")
    requests = relationship("TeacherRequest", back_populates="teacher")


class Subject(Base):
    """
    Represent the subjects studied in the database

    Fields:
        subject_code: Stores the subject code in the general structure of the college
        name: Human-readable name of the item
        curriculum: Relationship to access the curriculum which use this subject
        sessions: Relationship to access the sessions associated with the subject
        requests: Relationship to access the teacher requests for sessions associated with the subject
    """
    __tablename__ = "subjects"

    subject_code = Column(String, primary_key=True, unique=True, nullable=False)
    name = Column(String, nullable=True)

    # Relationships
    curriculums = relationship("Curriculum", back_populates="subject")
    sessions = relationship("Session", back_populates="subject")
    requests = relationship("TeacherRequest", back_populates="subject")


class Curriculum(Base):
    """
    The table in the database represents the curriculum for 1 academic semester

    Fields:
        semester_number: This is the semester number for a particular group,
                         by default if the group has no records in this table then it is equal to one (Primary Key)
        lectures_hours: Field storing the number of hours for lectures
        laboratory_hours: Field storing the number of hours for laboratory
        practical_hours: Field storing the number of hours for practical
        group_name: Foreign key field for linking to the groups table (Primary key)
        subject_code: Foreign key field for linking to the subjects table (Primary key)
        group: Relationship to access the group for which it was created curriculum
        subject: Relationship to access the subject for which it was created curriculum
    """
    __tablename__ = "curriculums"

    semester_number = Column(Integer, primary_key=True, nullable=False, default=1)
    # Numeric(x, y): x - quantity of integer places
    #                y - quantity of decimal places
    lectures_hours = Column(Numeric(5, 2), nullable=True)
    laboratory_hours = Column(Numeric(5, 2), nullable=True)
    practical_hours = Column(Numeric(5, 2), nullable=True)

    # Foreign keys
    group_name = Column(String, ForeignKey("groups.group_name", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True, nullable=False)
    subject_code = Column(String, ForeignKey("subjects.subject_code", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True, nullable=False)

    # Relationships
    group = relationship("Group", back_populates="curriculums")
    subject = relationship("Subject", back_populates="curriculums")


class Cabinet(Base):
    """
    Represents a cabinet in the database

    Fields:
        cabinet_number: The unique number of the cabinets in the one building (primary key)
        capacity: The meaning of how many people can fit in one cabinet
        cabinet_state: The current state of the cabinet (e.g., "Equipped with PC", "Repair")
        building_number: This is the foreign key of the building where the cabinet is located
        building: Relationship for access building where the cabinet is located
        sessions: Relationship to access the sessions associated with the cabinet
    """
    __tablename__ = "cabinets"

    cabinet_number = Column(Integer, primary_key=True, nullable=False)
    capacity = Column(Integer, nullable=True)
    cabinet_state = Column(String, nullable=True)

    # Foreign keys
    building_number = Column(Integer, ForeignKey("buildings.building_number", onupdate="CASCADE", ondelete="SET NULL"), primary_key=True)

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
        building_number: The unique number of the building (primary_key)
        city: The city where the building is located
        building_address: The building address
        cabinets: Relationship to access all cabinets associated with this building
    """
    __tablename__ = "buildings"

    building_number = Column(Integer, primary_key=True, nullable=False)
    city = Column(String, nullable=False, default="Орск")
    building_address = Column(String, nullable=False)

    # Relationships
    cabinets = relationship("Cabinet", back_populates="building")


class Session(Base):
    """
    Represents a one learn session in the database

    Fields:
        session_number: This is what number the session is on that day (Primary Key)
        date: This is the date of the session (Primary Key)
        session_type: This is the type of the session (e.g. "lecture" or "laboratory")
        group_name: Foreign key field for linking to the groups table (Primary Key)
        subject_code: Foreign key field for linking to the subjects table
        teacher_id: Foreign key field for linking to the teachers table
        cabinet_number: Foreign key field for linking to the cabinets table
        building_number: Second foreign key field for linking to the building number
        group: Relationship to access the group for which it was created session
        subject: Relationship to access the subject for which it was created session
        teacher: Relationship to access the teacher for which it was created session
        cabinet: Relationship to access the cabinet associated with this session
    """
    __tablename__ = "sessions"

    session_number = Column(Integer, primary_key=True, nullable=False)
    date = Column(Date, primary_key=True, nullable=False)
    session_type = Column(String, nullable=False)
    # Foreign keys
    group_name = Column(String, ForeignKey("groups.group_name", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    subject_code = Column(String, ForeignKey("subjects.subject_code", onupdate="CASCADE", ondelete="SET NULL"))
    teacher_id = Column(Integer, ForeignKey("teachers.id", onupdate="CASCADE", ondelete="SET NULL"))
    cabinet_number = Column(Integer, nullable=False)
    building_number = Column(Integer, nullable=False)

    # For a composite primary key
    __table_args__ = (
        ForeignKeyConstraint(
            ['cabinet_number', 'building_number'],
            ['cabinets.cabinet_number', 'cabinets.building_number'],
             onupdate="CASCADE", ondelete="SET NULL"
        ),
    )

    # Relationships
    group = relationship("Group", back_populates="sessions")
    subject = relationship("Subject", back_populates="sessions")
    teacher = relationship("Teacher", back_populates="sessions")
    cabinet = relationship(
        "Cabinet",
        primaryjoin="and_(Session.cabinet_number == Cabinet.cabinet_number, "
                    "Session.building_number == Cabinet.building_number)",
        back_populates="sessions"
        )


class EmploymentTeacher(Base):
    """
    Represents an employment teacher in the database

    Fields:
        date_start_period: This field stores the beginning of the period in which the teacher indicates his employment (Primary Key)
        date_end_period: This field stores the ending of the period in which the teacher indicates his employment (Primary Key)
        monday, tuesday, wednesday, thursday, friday, saturday: All fields with names of working days of the week -
            store the value of how much the teacher can work on this day.
            Also, it can take the value null - in this case it will be considered that in this period,
            on this day, the teacher will not be able to work
        teacher_id: Foreign key field for linking to the teachers table
        teacher: Relationship to access the teacher associated with this employment teacher
    """
    __tablename__ = "employment_teachers"

    date_start_period = Column(Date, primary_key=True, nullable=False)
    date_end_period = Column(Date, primary_key=True, nullable=False)
    monday = Column(String, nullable=True, default="8:30")
    tuesday = Column(String, nullable=True, default="8:30")
    wednesday = Column(String, nullable=True, default="8:30")
    thursday = Column(String, nullable=True, default="8:30")
    friday = Column(String, nullable=True, default="8:30")
    saturday = Column(String, nullable=True, default="8:30")

    # Foreign keys
    teacher_id = Column(Integer, ForeignKey("teachers.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)

    # Relationships
    teacher = relationship("Teacher", back_populates="employments")


class TeacherRequest(Base):
    """
    Represents a teacher request in the database

    Fields:
        date_request: This field stores the day that the teacher selects and the whole week will be counted from it.
            Thus, indicating the beginning of the week - the whole week is indicated
            and the teacher's request goes for the whole week (Primary Key)
        lectures_hours: Field storing the number of hours in request for lectures
        laboratory_hours: Field storing the number of hours in request  for laboratories
        practice_hours: Field storing the number of hours in request  for practices
        teacher_id: Foreign key field for linking to the teachers table
        subject_code: Foreign key field for linking to the subjects table
        group_name: Foreign key field for linking to the groups table
        teacher: Relationship to access the teacher associated with this request
        subject: Relationship to access the subject for which it was created session
        group: Relationship to access the group for which it was created session
    """
    __tablename__ = "teacher_requests"

    date_request = Column(Date, primary_key=True, nullable=False)
    lectures_hours = Column(Integer, nullable=False, default=0)
    laboratory_hours = Column(Integer, nullable=False, default=0)
    practice_hours = Column(Integer, nullable=False, default=0)

    # Foreign keys
    teacher_id = Column(Integer, ForeignKey("teachers.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    subject_code = Column(String, ForeignKey("subjects.subject_code", onupdate="CASCADE", ondelete="SET NULL"), primary_key=True)
    group_name = Column(String, ForeignKey("groups.group_name", onupdate="CASCADE", ondelete="SET NULL"), primary_key=True)

    # Relationships
    teacher = relationship("Teacher", back_populates="requests")
    subject = relationship("Subject", back_populates="requests")
    group = relationship("Group", back_populates="requests")
