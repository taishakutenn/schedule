"""
This file is the entry point to the api
"""

from fastapi import FastAPI
from fastapi.routing import APIRouter
import uvicorn

# Create fastapi app
app = FastAPI(title="OGTISheduleApi")

# Create main api router
main_api_router = APIRouter()

# Add main api router into fastapi app
app.include_router(main_api_router)

if __name__ == "__main__":
    # start local server
    uvicorn.run(app, host="0.0.0.0", port=8000)
