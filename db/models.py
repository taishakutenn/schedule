'''File for database models'''

from sqlalchemy import Column, String, Boolean, Integer, Numeric, ForeignKey, nullsfirst
from sqlalchemy.orm import relationship, DeclarativeBase, Relationship


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
    """
    __tablename__ = "groups"

    group_name = Column(String, primary_key=True, unique=True, nullable=False)
    quantity_students = Column(Integer, nullable=True)

    # Foreign keys
    group_advisor_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    speciality_code = Column(String, ForeignKey("specialties.speciality_code"), nullable=False)

    # Relationships
    advisor = relationship("Teacher", back_populates="advisory_group", uselist=False)  # uselist for one to one
    speciality = relationship("Speciality", back_populates="groups")
    curriculums = relationship("Curriculum", back_populates="group")


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
    """
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    fathername = Column(String, nullable=True)
    phone_number = Column(String, nullable=False)
    email = Column(String, nullable=True)

    # Relationships
    advisory_group = relationship("Group", back_populates="advisor")


class Subject(Base):
    """
    Represent the subjects studied in the database

    Fields:
        subject_code: Stores the subject code in the general structure of the college
        name: Human-readable name of the item
        curriculum: Relationship to access the curriculum which use this subject
    """
    __tablename__ = "subjects"

    subject_code = Column(String, primary_key=True, unique=True, nullable=False)
    name = Column(String, nullable=True)

    # Relationships
    curriculums = relationship("Curriculum", back_populates="subject")


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
    group_name = Column(String, ForeignKey("groups.group_name"), primary_key=True, nullable=False)
    subject_code = Column(String, ForeignKey("subjects.subject_code"), primary_key=True, nullable=False)

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
    """
    __tablename__ = "cabinets"

    cabinet_number = Column(Integer, primary_key=True, nullable=False)
    capacity = Column(Integer, nullable=True)
    cabinet_state = Column(String, nullable=True)

    # Foreign keys
    building_number = Column(Integer, ForeignKey("buildings.building_number"))

    # Relationships
    building = relationship("Building", back_populates="cabinets")


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
