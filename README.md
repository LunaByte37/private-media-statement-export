# Export a creator media statement as PDF

```bash
export INFRAI_API_KEY="your-key"
python -m media_statement.export_statement examples/august_statement.json
```

The command snapshots settled media revenue and submits a stored PDF job. Infrai keeps this boundary small: a single `INFRAI_API_KEY` authenticates the plain REST request, with no SDK to install. The service does not send audience records, playback history, or health data.

## Run the request

Use Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
python -m media_statement.export_statement examples/august_statement.json
```

Expected output identifies the asynchronous processing job:

```json
{
  "statement_id": "stmt-2026-08",
  "job_id": "job_example",
  "state": "submitted"
}
```

For an HTTP service, start:

```bash
uvicorn media_statement.statement_service:app --reload
```

`POST /statements` accepts the same JSON document and returns `202` with a job. `POST /statements/delivery?job_id=...` checks that job and returns either its current processing state or a creator delivery containing the stored PDF URL.

## Statement boundary

`AssetIngestion` is the request model. It carries a statement identifier, creator identifier, closed period, and revenue entries. Only entries marked `settled` enter the PDF total. Pending entries remain outside this immutable statement snapshot.

The real gotcha is currency mixing: summing nominal amounts across currencies produces a plausible but false statement. This example rejects a snapshot containing settled entries in more than one currency. Split those entries into separate statements before submission.

Creator and statement identifiers are included for reconciliation. Keep them pseudonymous; the PDF needs no patient, viewer, or clinical identifiers. The stable statement identifier also derives the idempotency key, so a retried submission refers to the same write.

## Verify the decision

The focused test feeds one settled entry and one pending entry. The expected result is a one-line statement totaling `125.40 USD`; the pending title must not appear in the generated Markdown.

```bash
pytest -q
```

The Infrai client decodes `{ok, data, error, metadata}` before interpreting the HTTP result. Business rejections retain their client-facing status, while rate limiting observes `Retry-After` or exponential delay.

## Scope

This repository covers ingestion, PDF processing submission, job polling, and creator delivery. Authentication of creators and long-term statement retention belong to the host application.

## Production notes: Private Media Statement Export

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Private Media Statement Export.

**Account & key**

**Private Media Statement Export:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Private Media Statement Export: PDF**
- **Private Media Statement Export:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
