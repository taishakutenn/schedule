"""
This file is the entry point to the api
"""

from fastapi import FastAPI
from fastapi.routing import APIRouter
import uvicorn

#from api.handlers import, building_router, cabinet_router, subject_router, curriculum_router, speciality_router, group_router, request_router, employment_router, session_router, teachers_groups_router, teachers_subjects_router
from api.handlers import category_router, teacher_router, building_router, cabinet_router, session_type_router, speciality_router, plan_router, semester_router, chapter_router, \
                         cycle_router, module_router, subject_in_cycle_router, subject_in_cycle_hours_router, certification_router

# Create fastapi app
app = FastAPI(title="OGTIScheduleApi")

# Create main api router
main_api_router = APIRouter()

# Add child routers to the main
main_api_router.include_router(teacher_router, prefix="/teachers", tags=["teacher"])
main_api_router.include_router(building_router, prefix="/buildings", tags=["building"])
main_api_router.include_router(cabinet_router, prefix="/cabinets", tags=["cabinet"])
main_api_router.include_router(speciality_router, prefix="/specialities", tags=["speciality"])
# main_api_router.include_router(group_router, prefix="/groups", tags=["group"])
# main_api_router.include_router(subject_router, prefix="/subjects", tags=["subject"])
# main_api_router.include_router(curriculum_router, prefix="/curriculums", tags=["curriculum"])
# main_api_router.include_router(employment_router, prefix="/employments", tags=["employment"])
# main_api_router.include_router(request_router, prefix="/requests", tags=["request"])
# main_api_router.include_router(session_router, prefix="/sessions", tags=["session"])
# main_api_router.include_router(teachers_groups_router, prefix="/teachers-groups", tags=["teachers-groups"])
# main_api_router.include_router(teachers_subjects_router, prefix="/teachers-subjects", tags=["teachers-subjects"])
main_api_router.include_router(category_router, prefix="/teacher-category", tags=["teacher-category"])
main_api_router.include_router(session_type_router, prefix="/session-type", tags=["session-type"])
main_api_router.include_router(plan_router, prefix="/plans", tags=["plans"])
main_api_router.include_router(semester_router, prefix="/semesters", tags=["semesters"])
main_api_router.include_router(chapter_router, prefix="/chapters", tags=["chapters"])
main_api_router.include_router(cycle_router, prefix="/cycles", tags=["cycles"])
main_api_router.include_router(module_router, prefix="/modules", tags=["modules"])
main_api_router.include_router(subject_in_cycle_router, prefix="/subjects_in_cycles", tags=["subject-in-cycle"])
main_api_router.include_router(subject_in_cycle_hours_router, prefix="/subjects_in_cycles_hours", tags=["subjects-in-cycles-hours"])
main_api_router.include_router(certification_router, prefix="/certifications", tags=["certifications"])



# Add main api router into fastapi app
app.include_router(main_api_router)

if __name__ == "__main__":
    # start local server
    uvicorn.run(app, host="0.0.0.0", port=8000)
