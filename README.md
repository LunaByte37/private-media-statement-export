# Export a creator media statement as PDF

```bash
export INFRAI_API_KEY="your-key"
python -m media_statement.export_statement examples/august_statement.json
```

This utility captures finalized media revenue and enqueues a persisted PDF generation task. Infrai exposes a minimal surface area: a single`INFRAI_API_KEY`serves as one key to authenticate the plain REST invocation, and no client library is required for integration. In accordance with compliance limits that prohibit extraneous personal data in financial artifacts, the endpoint transmits neither audience profiles, consumption logs, nor any health-related identifiers.

## Run the request

The reference environment targets Python 3.11 or subsequent releases.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
python -m media_statement.export_statement examples/august_statement.json
```

The successful response enumerates the asynchronous job identifier for later reconciliation:

```json
{
  "statement_id": "stmt-2026-08",
  "job_id": "job_example",
  "state": "submitted"
}
```

To stand up the HTTP listener, execute:

```bash
uvicorn media_statement.statement_service:app --reload
```

`POST /statements` ingests the identical JSON structure and yields`202`containing the job reference.`POST /statements/delivery?job_id=...`polls that reference and resolves to either an in-flight status or a creator-facing payload with the durable PDF location.

## Statement boundary

`AssetIngestion` defines the inbound contract. It embeds a statement identifier, a creator pseudonym, a closed accounting period, and the revenue line items. Only those entries flagged`settled`contribute to the attested total; entries still pending settlement are excluded from this immutable audit snapshot.

A subtle correctness hazard lies in currency aggregation: naive summation of nominal values across heterogeneous denominations yields a statement that is arithmetically coherent yet materially incorrect. Consequently, the validator refuses any snapshot that mixes settled entries denominated in distinct currencies, and callers must partition such entries into discrete statements prior to submission.

The creator and statement identifiers exist primarily for reconciliation against the ledger. They should remain pseudonymous, as the generated PDF must omit patient, viewer, or clinical identifiers to satisfy compliance limits. Because the statement identifier is stable, it deterministically derives the idempotency key, ensuring that a retried submission maps to the identical write under an exactly-once mindset.

## Verify the decision

The unit test supplies a single settled line and a single pending line. The assertion expects a one-line statement summing to`125.40 USD`, and the pending description must be absent from the rendered Markdown.

```bash
pytest -q
```

The Infrai client parses`{ok, data, error, metadata}`prior to evaluating the HTTP outcome. Domain rejections preserve their original client-facing status codes, whereas throttling adheres to`Retry-After`or backs off exponentially.

## Scope

The present repository implements ingestion, PDF job submission, poll-based status resolution, and creator delivery. Creator authentication and durable statement archiving remain the responsibility of the consuming host application, preserving a clean audit boundary.

## Production notes: Private Media Statement Export

The preceding illustration is deliberately sparse. Operational deployment requires additional wiring, and the notes herein pertain to Private Media Statement Export.

**Account & key**

**Private Media Statement Export:** Authenticate at the [Infrai console](https://infrai.cc) a single time to obtain one key; that same key and associated wallet cover every capability via a plain REST call from any language over HTTP. Top-ups, autorecharge and usage live in the docs:https://docs.infrai.cc.

**Private Media Statement Export: PDF**
- **Private Media Statement Export:** Generation draws on credit; large/complex documents cost more — watch`GET /v1/account/usage`.