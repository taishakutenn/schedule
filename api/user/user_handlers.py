from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from api.user.user_pydantic import *
from db.session import get_db
from api.user.user_services import UserService

user_router = APIRouter()
user_service = UserService()


@user_router.post("/create", response_model=ShowUser, status_code=201)
async def create_user(body: CreateUser, db: AsyncSession = Depends(get_db)):
    return await user_service._create_new_user(body, db)


@user_router.get("/search/by_email/{email}", response_model=ShowUser, status_code=200)
async def get_user_by_email(email: EmailStr, db: AsyncSession = Depends(get_db)):
    return await user_service._get_user_by_email(email, db)