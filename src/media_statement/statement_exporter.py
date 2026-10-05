import hashlib
import html
from decimal import Decimal
from typing import Any

from .infrai_pdf import InfraiPdfClient
from .statement_models import AssetIngestion, CreatorDelivery, EntryStatus, ProcessingJob


class StatementNotReady(ValueError):
    pass


def prepare_statement(asset: AssetIngestion) -> tuple[str, int, Decimal, str]:
    if asset.period_end < asset.period_start:
        raise StatementNotReady("period_end must be on or after period_start")
    settled = [entry for entry in asset.entries if entry.status == EntryStatus.SETTLED]
    if not settled:
        raise StatementNotReady("at least one settled entry is required")
    currencies = {entry.currency for entry in settled}
    if len(currencies) != 1:
        raise StatementNotReady("settled entries must use one currency")

    currency = next(iter(currencies))
    total = sum((entry.amount for entry in settled), Decimal("0"))
    rows = "\n".join(
        f"| {entry.service_date} | {html.escape(entry.asset_title)} | "
        f"{html.escape(entry.platform)} | {entry.amount:.2f} {currency} |"
        for entry in settled
    )
    markdown = (
        f"# Media account statement\n\n"
        f"Statement: `{html.escape(asset.statement_id)}`  \n"
        f"Creator: `{html.escape(asset.creator_id)}`  \n"
        f"Period: {asset.period_start} to {asset.period_end}\n\n"
        f"| Date | Asset | Platform | Amount |\n|---|---|---|---:|\n{rows}\n\n"
        f"**Settled total: {total:.2f} {currency}**\n"
    )
    return markdown, len(settled), total, currency


class StatementExporter:
    def __init__(self, client: InfraiPdfClient) -> None:
        self.client = client

    def submit(self, asset: AssetIngestion) -> CreatorDelivery:
        markdown, count, total, currency = prepare_statement(asset)
        idempotency_key = hashlib.sha256(f"statement:{asset.statement_id}".encode()).hexdigest()
        data = self.client.generate(markdown, idempotency_key)
        return CreatorDelivery(
            statement_id=asset.statement_id,
            creator_id=asset.creator_id,
            pdf_url=str(data["url"]),
            included_entries=count,
            total=total,
            currency=currency,
        )

    def deliver(self, asset: AssetIngestion, job: ProcessingJob) -> CreatorDelivery | None:
        markdown, count, total, currency = prepare_statement(asset)
        del markdown
        data: dict[str, Any] = self.client.get_job(job.job_id)
        if data.get("status") not in {"completed", "succeeded"}:
            return None
        return CreatorDelivery(
            statement_id=asset.statement_id,
            creator_id=asset.creator_id,
            pdf_url=str(data["url"]),
            included_entries=count,
            total=total,
            currency=currency,
        )
