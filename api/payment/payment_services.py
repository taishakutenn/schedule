from api.payment.payment_pydantic import *
from api.services_helpers import ensure_payment_form_exists, ensure_payment_form_unique
from api.payment.payment_DAL import PaymentFormDAL
from fastapi import HTTPException, Request

from config.logging_config import configure_logging

# Create logger object
logger = configure_logging()


class PaymentService:
    async def _create_new_payment_form(self, body: CreatePaymentForm, request: Request, db) -> ShowPaymentFormWithHATEOAS:
        async with db as session:
            async with session.begin():
                payment_form_dal = PaymentFormDAL(session)
                try:
                    if not await ensure_payment_form_unique(payment_form_dal, body.payment_name):
                        raise HTTPException(status_code=400, detail=f"Форма оплаты '{body.payment_name}' уже существует")

                    payment_form = await payment_form_dal.create_payment_form(
                        payment_name=body.payment_name
                    )
                    payment_name = payment_form.payment_name
                    payment_form_pydantic = ShowPaymentForm.model_validate(payment_form, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/payment-forms/search/by_name/{payment_name}',
                        "update": f'{api_base_url}/payment-forms/update',
                        "delete": f'{api_base_url}/payment-forms/delete/{payment_name}',
                        "payment_forms": f'{api_base_url}/payment-forms',
                        "groups": f'{api_base_url}/groups/search/by_payment_form/{payment_name}'
                    }

                    return ShowPaymentFormWithHATEOAS(payment_form=payment_form_pydantic, links=hateoas_links)

                except HTTPException:
                    await session.rollback()
                    raise
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Неожиданная ошибка при создании формы оплаты '{body.payment_name}': {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_payment_form_by_name(self, payment_name: str, request: Request, db) -> ShowPaymentFormWithHATEOAS:
        async with db as session:
            async with session.begin():
                payment_form_dal = PaymentFormDAL(session)
                try:
                    payment_form = await payment_form_dal.get_payment_form(payment_name)
                    if not payment_form:
                        raise HTTPException(status_code=404, detail=f"Форма оплаты с именем '{payment_name}' не найдена")
                    payment_form_pydantic = ShowPaymentForm.model_validate(payment_form, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/payment-forms/search/by_name/{payment_name}',
                        "update": f'{api_base_url}/payment-forms/update',
                        "delete": f'{api_base_url}/payment-forms/delete/{payment_name}',
                        "payment_forms": f'{api_base_url}/payment-forms',
                        "groups": f'{api_base_url}/groups/search/by_payment_form/{payment_name}'
                    }

                    return ShowPaymentFormWithHATEOAS(payment_form=payment_form_pydantic, links=hateoas_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение формы оплаты '{payment_name}' отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _get_all_payment_forms(self, page: int, limit: int, request: Request, db) -> ShowPaymentFormListWithHATEOAS:
        async with db as session:
            async with session.begin():
                payment_form_dal = PaymentFormDAL(session)
                try:
                    payment_forms = await payment_form_dal.get_all_payment_forms(page, limit)
                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    payment_forms_with_hateoas = []
                    for payment_form in payment_forms:
                        payment_form_pydantic = ShowPaymentForm.model_validate(payment_form, from_attributes=True)
                        payment_name = payment_form.payment_name
                        payment_form_links = {
                            "self": f'{api_base_url}/payment-forms/search/by_name/{payment_name}',
                            "update": f'{api_base_url}/payment-forms/update',
                            "delete": f'{api_base_url}/payment-forms/delete/{payment_name}',
                            "payment_forms": f'{api_base_url}/payment-forms',
                            "groups": f'{api_base_url}/groups/search/by_payment_form/{payment_name}'
                        }
                        payment_form_with_links = ShowPaymentFormWithHATEOAS(payment_form=payment_form_pydantic, links=payment_form_links)
                        payment_forms_with_hateoas.append(payment_form_with_links)

                    collection_links = {
                        "self": f'{api_base_url}/payment-forms/search?page={page}&limit={limit}',
                        "create": f'{api_base_url}/payment-forms/create'
                    }
                    collection_links = {k: v for k, v in collection_links.items() if v is not None}

                    return ShowPaymentFormListWithHATEOAS(payment_forms=payment_forms_with_hateoas, links=collection_links)

                except HTTPException:
                    raise
                except Exception as e:
                    logger.warning(f"Получение форм оплаты отменено (Ошибка: {e})")
                    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера.")


    async def _delete_payment_form(self, payment_name: str, request: Request, db) -> ShowPaymentFormWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    payment_form_dal = PaymentFormDAL(session)
                    if not await ensure_payment_form_exists(payment_form_dal, payment_name):
                        raise HTTPException(status_code=404, detail=f"Форма оплаты с именем '{payment_name}' не найдена")

                    payment_form = await payment_form_dal.delete_payment_form(payment_name)
                    if not payment_form:
                        raise HTTPException(status_code=404, detail=f"Форма оплаты с именем '{payment_name}' не найдена")

                    payment_form_pydantic = ShowPaymentForm.model_validate(payment_form, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "payment_forms": f'{api_base_url}/payment-forms',
                        "create": f'{api_base_url}/payment-forms/create'
                    }
                    hateoas_links = {k: v for k, v in hateoas_links.items() if v is not None}

                    return ShowPaymentFormWithHATEOAS(payment_form=payment_form_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.error(f"Неожиданная ошибка при удалении формы оплаты '{payment_name}': {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера при удалении формы оплаты.")


    async def _update_payment_form(self, body: UpdatePaymentForm, request: Request, db) -> ShowPaymentFormWithHATEOAS:
        async with db as session:
            try:
                async with session.begin():
                    payment_form_dal = PaymentFormDAL(session)

                    update_data = {key: value for key, value in body.dict().items() if value is not None and key not in ["payment_name", "new_payment_name"]}

                    target_payment_name = body.payment_name
                    if body.new_payment_name is not None:
                        update_data["payment_name"] = body.new_payment_name
                        target_payment_name = body.new_payment_name
                        
                        if not await ensure_payment_form_unique(payment_form_dal, target_payment_name):
                            raise HTTPException(status_code=400, detail=f"Форма оплаты '{target_payment_name}' уже существует")

                    if not await ensure_payment_form_exists(payment_form_dal, body.payment_name):
                        raise HTTPException(status_code=404, detail=f"Форма оплаты с именем '{body.payment_name}' не найдена")

                    payment_form = await payment_form_dal.update_payment_form(target_name=body.payment_name, **update_data)
                    if not payment_form:
                        raise HTTPException(status_code=404, detail=f"Форма оплаты с именем '{body.payment_name}' не найдена")

                    payment_name = payment_form.payment_name 
                    payment_form_pydantic = ShowPaymentForm.model_validate(payment_form, from_attributes=True)

                    base_url = str(request.base_url).rstrip('/')
                    api_prefix = ''
                    api_base_url = f'{base_url}{api_prefix}'

                    hateoas_links = {
                        "self": f'{api_base_url}/payment-forms/search/by_name/{payment_name}',
                        "update": f'{api_base_url}/payment-forms/update',
                        "delete": f'{api_base_url}/payment-forms/delete/{payment_name}',
                        "payment_forms": f'{api_base_url}/payment-forms',
                        "groups": f'{api_base_url}/groups/search/by_payment_form/{payment_name}'
                    }

                    return ShowPaymentFormWithHATEOAS(payment_form=payment_form_pydantic, links=hateoas_links)

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                logger.warning(f"Изменение данных о форме оплаты отменено (Ошибка: {e})")
                raise e
                    