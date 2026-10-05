from decimal import Decimal
from unittest.mock import patch

from media_statement.infrai_pdf import InfraiPdfClient
from media_statement.statement_exporter import StatementExporter, prepare_statement
from media_statement.statement_models import AssetIngestion


def test_statement_includes_only_settled_revenue() -> None:
    asset = AssetIngestion.model_validate(
        {
            "statement_id": "stmt-2026-08",
            "creator_id": "creator-17",
            "period_start": "2026-08-01",
            "period_end": "2026-08-31",
            "entries": [
                {
                    "asset_title": "Cardiac rehab series",
                    "platform": "Stream North",
                    "service_date": "2026-08-04",
                    "amount": "125.40",
                    "currency": "USD",
                    "status": "settled",
                },
                {
                    "asset_title": "Sleep clinic interview",
                    "platform": "Stream North",
                    "service_date": "2026-08-28",
                    "amount": "88.10",
                    "currency": "USD",
                    "status": "pending",
                },
            ],
        }
    )

    markdown, count, total, currency = prepare_statement(asset)

    assert count == 1
    assert total == Decimal("125.40")
    assert currency == "USD"
    assert "Cardiac rehab series" in markdown
    assert "Sleep clinic interview" not in markdown


def test_submit_uses_body_idempotency_and_completed_pdf() -> None:
    asset = AssetIngestion.model_validate_json(
        '{"statement_id":"stmt-1","creator_id":"creator-1",'
        '"period_start":"2026-08-01","period_end":"2026-08-31",'
        '"entries":[{"asset_title":"Title","platform":"Platform",'
        '"service_date":"2026-08-04","amount":"125.40",'
        '"currency":"USD","status":"settled"}]}'
    )
    client = InfraiPdfClient("test-key")

    with patch.object(client, "_request", return_value={"url": "https://example.test/file.pdf"}) as request:
        delivery = StatementExporter(client).submit(asset)

    assert delivery.pdf_url == "https://example.test/file.pdf"
    assert delivery.total == Decimal("125.40")
    assert delivery.included_entries == 1
    args, _ = request.call_args
    assert args[:2] == ("POST", "/v1/pdf/generate")
    assert args[2]["idempotency_key"]
    assert len(args) == 3
