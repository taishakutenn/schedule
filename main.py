"""
This file is the entry point to the api
"""

from fastapi import FastAPI
from fastapi.routing import APIRouter
import uvicorn

from api.handlers import teacher_router

# Create fastapi app
app = FastAPI(title="OGTISheduleApi")

# Create main api router
main_api_router = APIRouter()

# Add child routers to the main
main_api_router.include_router(teacher_router, prefix="/teacher", tags=["teacher"])

# Add main api router into fastapi app
app.include_router(main_api_router)

if __name__ == "__main__":
    # start local server
    uvicorn.run(app, host="0.0.0.0", port=8000)
