from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class EntryStatus(StrEnum):
    SETTLED = "settled"
    PENDING = "pending"


class RevenueEntry(BaseModel):
    asset_title: str
    platform: str
    service_date: date
    amount: Decimal
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    status: EntryStatus


class AssetIngestion(BaseModel):
    statement_id: str = Field(min_length=1)
    creator_id: str = Field(min_length=1)
    period_start: date
    period_end: date
    entries: list[RevenueEntry] = Field(min_length=1)


class ProcessingJob(BaseModel):
    statement_id: str
    job_id: str
    state: str


class CreatorDelivery(BaseModel):
    statement_id: str
    creator_id: str
    pdf_url: str
    included_entries: int
    total: Decimal
    currency: str
