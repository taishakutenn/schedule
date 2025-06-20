'''File for database models'''

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


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
    name = Column(String, nallable=False)
    surname = Column(String, nallable=False)
    fathername = Column(String, nallable=True)
    phone_number = Column(String, nullable=False)
    email = Column(String, nullable=True)

    # Relationships
    advisory_group = relationship("Group", back_populates="advisor")
