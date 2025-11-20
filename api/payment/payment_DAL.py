from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import PaymentForm
from config.decorators import log_exceptions

class PaymentFormDAL:
    """Data Access Layer for operating payment form info"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    @log_exceptions
    async def create_payment_form(self, payment_name: str) -> PaymentForm:
        new_payment_form = PaymentForm(
            payment_name=payment_name
        )
        self.db_session.add(new_payment_form)
        await self.db_session.flush()
        return new_payment_form

    @log_exceptions
    async def delete_payment_form(self, payment_name: str) -> PaymentForm | None:
        query = delete(PaymentForm).where(PaymentForm.payment_name == payment_name).returning(PaymentForm)
        res = await self.db_session.execute(query)
        deleted_payment_form = res.scalar_one_or_none()
        return deleted_payment_form

    @log_exceptions
    async def get_all_payment_forms(self, page: int, limit: int) -> list[PaymentForm]:
        if page == 0:
            query = select(PaymentForm).order_by(PaymentForm.payment_name.asc())
        else:
            query = select(PaymentForm).offset((page - 1) * limit).limit(limit)
        result = await self.db_session.execute(query)
        payment_forms = list(result.scalars().all())
        return payment_forms

    @log_exceptions
    async def get_payment_form(self, payment_name: str) -> PaymentForm | None:
        query = select(PaymentForm).where(PaymentForm.payment_name == payment_name)
        res = await self.db_session.execute(query)
        payment_form_row = res.scalar_one_or_none()
        return payment_form_row

    @log_exceptions
    async def update_payment_form(self, target_name: str, **kwargs) -> PaymentForm | None:
        query = update(PaymentForm).where(PaymentForm.payment_name == target_name).values(**kwargs).returning(PaymentForm)
        res = await self.db_session.execute(query)
        updated_payment_form = res.scalar_one_or_none()
        return updated_payment_form