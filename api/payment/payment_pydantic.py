from typing import List
from api.models import TunedModel


class ShowPaymentForm(TunedModel):
    """Class for get payment form info"""
    payment_name: str


class CreatePaymentForm(TunedModel):
    payment_name: str


class UpdatePaymentForm(TunedModel):
    payment_name: str
    new_payment_name: str | None = None


class ShowPaymentFormWithHATEOAS(TunedModel):
    payment_form: ShowPaymentForm
    links: dict[str, str] = {}


class ShowPaymentFormListWithHATEOAS(TunedModel):
    payment_forms: List[ShowPaymentFormWithHATEOAS]
    links: dict[str, str] = {}