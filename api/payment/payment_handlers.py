from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from api.payment.payment_pydantic import *
from api.models import QueryParams
from db.session import get_db
from api.payment.payment_services import PaymentService

payment_form_router = APIRouter()

payment_service = PaymentService()


@payment_form_router.post("/create", response_model=ShowPaymentFormWithHATEOAS, status_code=201)
async def create_payment_form(body: CreatePaymentForm, request: Request, db: AsyncSession = Depends(get_db)):
    return await payment_service._create_new_payment_form(body, request, db)


@payment_form_router.get("/search/by_name/{payment_name}", response_model=ShowPaymentFormWithHATEOAS, responses={404: {"description": "Форма оплаты не найдена"}})
async def get_payment_form_by_name(payment_name: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await payment_service._get_payment_form_by_name(payment_name, request, db)


@payment_form_router.get("/search", response_model=ShowPaymentFormListWithHATEOAS)
async def get_all_payment_forms(query_param: Annotated[QueryParams, Depends()], request: Request, db: AsyncSession = Depends(get_db)):
    return await payment_service._get_all_payment_forms(query_param.page, query_param.limit, request, db)


@payment_form_router.delete("/delete/{payment_name}", response_model=ShowPaymentFormWithHATEOAS, responses={404: {"description": "Форма оплаты не найдена"}})
async def delete_payment_form(payment_name: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await payment_service._delete_payment_form(payment_name, request, db)


@payment_form_router.put("/update", response_model=ShowPaymentFormWithHATEOAS, responses={404: {"description": "Форма оплаты не найдена"}})
async def update_payment_form(body: UpdatePaymentForm, request: Request, db: AsyncSession = Depends(get_db)):
    return await payment_service._update_payment_form(body, request, db)
