from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from datetime import date
from db.session import get_db

from sqlalchemy.ext.asyncio import AsyncSession
from api.schedule.schedule_services import ScheduleService

schedule_router = APIRouter()
schedule_service = ScheduleService()

@schedule_router.get("/search/sessions/report/for-group/{group_name}/{period_start_date}", status_code=200)
async def get_sessions_report_by_group(group_name: str, period_start_date: date, AsyncSession = Depends(get_db)):
    return await schedule_service._get_sessions_report_by_group(group_name, period_start_date, AsyncSession)

@schedule_router.post("/copy/schedule/{start_copy_period_date}/{start_period_date}/{count_days}", status_code=200)
async def copy_schedule_in_range(start_copy_period_date: date, start_period_date: date, count_days: int, AsyncSession = Depends(get_db)):
    return await schedule_service._copy_all_schedule(start_copy_period_date, start_period_date, count_days, AsyncSession)