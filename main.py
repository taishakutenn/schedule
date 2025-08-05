"""
This file is the entry point to the api
"""

from fastapi import FastAPI
from fastapi.routing import APIRouter
import uvicorn

from api.handlers import teacher_router, building_router, cabinet_router, subject_router, curriculum_router, speciality_router, group_router, request_router, employment_router

# Create fastapi app
app = FastAPI(title="OGTIScheduleApi")

# Create main api router
main_api_router = APIRouter()

# Add child routers to the main
main_api_router.include_router(teacher_router, prefix="/teacher", tags=["teacher"])
main_api_router.include_router(building_router, prefix="/building", tags=["building"])
main_api_router.include_router(cabinet_router, prefix="/cabinet", tags=["cabinet"])
main_api_router.include_router(speciality_router, prefix="/speciality", tags=["speciality"])
main_api_router.include_router(group_router, prefix="/group", tags=["group"])
main_api_router.include_router(subject_router, prefix="/subject", tags=["subject"])
main_api_router.include_router(curriculum_router, prefix="/curriculum", tags=["curriculum"])
main_api_router.include_router(employment_router, prefix="/employment", tags=["employment"])
main_api_router.include_router(curriculum_router, prefix="/request", tags=["request"])

# Add main api router into fastapi app
app.include_router(main_api_router)

if __name__ == "__main__":
    # start local server
    uvicorn.run(app, host="0.0.0.0", port=8000)
