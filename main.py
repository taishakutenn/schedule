"""
This file is the entry point to the api
"""

from fastapi import FastAPI
from fastapi.routing import APIRouter
import uvicorn

from api.teacher_category.teacher_category_handlers import category_router
from api.teacher.teacher_handlers import teacher_router
from api.building.building_handlers import building_router
from api.cabinet.cabinet_handlers import cabinet_router
from api.speciality.speciality_handlers import speciality_router
from api.group.group_handlers import group_router
from api.session_type.session_type_handlers import session_type_router
from api.session.session_handlers import session_router
from api.teacher_in_plan.teacher_in_plan_handlers import teacher_in_plan_router
from api.subject_in_cycle_hours.subject_in_cycle_hours_handlers import subject_in_cycle_hours_router
from api.subject_in_cycle.subject_in_cycle_handlers import subject_in_cycle_router
from api.module.module_handlers import module_router
from api.cycle.cycle_handlers import cycle_router
from api.chapter.chapter_handlers import chapter_router
from api.plan.plan_handlers import plan_router
from api.semester.semester_handlers import semester_router
from api.certification.certification_handlers import certification_router
from api.stream.stream_handlers import stream_router
from api.teacher_building.teacher_building_handlers import teacher_building_router

# Create fastapi app
app = FastAPI(title="OGTIScheduleApi")

# Create main api router
main_api_router = APIRouter()

# Add child routers to the main
# main_api_router.include_router(building_router, prefix="/buildings", tags=["buildings"])
# main_api_router.include_router(cabinet_router, prefix="/cabinets", tags=["cabinets"])
# main_api_router.include_router(speciality_router, prefix="/specialities", tags=["specialities"])
# main_api_router.include_router(group_router, prefix="/groups", tags=["groups"])
# main_api_router.include_router(subject_router, prefix="/subjects", tags=["subject"])
# main_api_router.include_router(curriculum_router, prefix="/curriculums", tags=["curriculum"])
# main_api_router.include_router(employment_router, prefix="/employments", tags=["employment"])
# main_api_router.include_router(request_router, prefix="/requests", tags=["request"])
# main_api_router.include_router(session_router, prefix="/sessions", tags=["sessions"])
# main_api_router.include_router(teachers_groups_router, prefix="/teachers-groups", tags=["teachers-groups"])
# main_api_router.include_router(teachers_subjects_router, prefix="/teachers-subjects", tags=["teachers-subjects"])
# main_api_router.include_router(category_router, prefix="/teacher-category", tags=["teacher-category"])
# main_api_router.include_router(session_type_router, prefix="/session-type", tags=["session-type"])
# main_api_router.include_router(plan_router, prefix="/plans", tags=["plans"])
# main_api_router.include_router(semester_router, prefix="/semesters", tags=["semesters"])
# main_api_router.include_router(chapter_router, prefix="/chapters", tags=["chapters"])
# main_api_router.include_router(cycle_router, prefix="/cycles", tags=["cycles"])
# main_api_router.include_router(module_router, prefix="/modules", tags=["modules"])
# main_api_router.include_router(subject_in_cycle_router, prefix="/subjects_in_cycles", tags=["subject-in-cycle"])
# main_api_router.include_router(subject_in_cycle_hours_router, prefix="/subjects_in_cycles_hours", tags=["subjects-in-cycles-hours"])
# main_api_router.include_router(certification_router, prefix="/certifications", tags=["certifications"])
# main_api_router.include_router(teacher_in_plan_router, prefix="/teachers_in_plans", tags=["teachers-in-plans"])
# main_api_router.include_router(teacher_building_router, prefix="/teachers_buildings", tags=["teachers-buildings"])
# main_api_router.include_router(stream_router, prefix="/streams", tags=["streams"])




# Test routers from entity
main_api_router.include_router(category_router, prefix="/teacher-category", tags=["teacher-category"])
main_api_router.include_router(teacher_router, prefix="/teachers", tags=["teachers"])
main_api_router.include_router(building_router, prefix="/buildings", tags=["buildings"])
main_api_router.include_router(cabinet_router, prefix="/cabinets", tags=["cabinets"])
main_api_router.include_router(speciality_router, prefix="/specialities", tags=["specialities"])
main_api_router.include_router(group_router, prefix="/groups", tags=["groups"])
main_api_router.include_router(session_type_router, prefix="/session-type", tags=["session-type"])
main_api_router.include_router(session_router, prefix="/sessions", tags=["sessions"])
main_api_router.include_router(teacher_in_plan_router, prefix="/teachers_in_plans", tags=["teachers-in-plans"])
main_api_router.include_router(subject_in_cycle_hours_router, prefix="/subjects_in_cycles_hours", tags=["subjects-in-cycles-hours"])
main_api_router.include_router(subject_in_cycle_router, prefix="/subjects_in_cycles", tags=["subject-in-cycle"])
main_api_router.include_router(module_router, prefix="/modules", tags=["modules"])
main_api_router.include_router(cycle_router, prefix="/cycles", tags=["cycles"])
main_api_router.include_router(chapter_router, prefix="/chapters", tags=["chapters"])
main_api_router.include_router(plan_router, prefix="/plans", tags=["plans"])
main_api_router.include_router(semester_router, prefix="/semesters", tags=["semesters"])
main_api_router.include_router(certification_router, prefix="/certifications", tags=["certifications"])
main_api_router.include_router(stream_router, prefix="/streams", tags=["streams"])
main_api_router.include_router(teacher_building_router, prefix="/teachers_buildings", tags=["teachers-buildings"])

# Add main api router into fastapi app
app.include_router(main_api_router)

if __name__ == "__main__":
    # start local server
    uvicorn.run(app, host="0.0.0.0", port=8000)
