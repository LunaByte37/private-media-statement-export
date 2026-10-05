import os

from fastapi import FastAPI, HTTPException

from .infrai_pdf import InfraiError, InfraiPdfClient, InfraiTransportError
from .statement_exporter import StatementExporter, StatementNotReady
from .statement_models import AssetIngestion, CreatorDelivery, ProcessingJob

app = FastAPI(title="Media statement export")


def exporter() -> StatementExporter:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="INFRAI_API_KEY is required")
    return StatementExporter(InfraiPdfClient(api_key))


@app.post("/statements", response_model=CreatorDelivery)
def create_statement(asset: AssetIngestion) -> CreatorDelivery:
    try:
        return exporter().submit(asset)
    except StatementNotReady as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except InfraiError as exc:
        client_status = exc.status if 400 <= exc.status < 500 else 502
        raise HTTPException(status_code=client_status, detail={"code": exc.code, "error": exc.detail}) from exc
    except InfraiTransportError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/statements/delivery", response_model=CreatorDelivery, responses={202: {"model": ProcessingJob}})
def get_delivery(asset: AssetIngestion, job_id: str) -> CreatorDelivery | ProcessingJob:
    job = ProcessingJob(statement_id=asset.statement_id, job_id=job_id, state="processing")
    try:
        delivery = exporter().deliver(asset, job)
    except StatementNotReady as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except InfraiError as exc:
        client_status = exc.status if 400 <= exc.status < 500 else 502
        raise HTTPException(status_code=client_status, detail={"code": exc.code, "error": exc.detail}) from exc
    except InfraiTransportError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if delivery is None:
        return job
    return delivery
