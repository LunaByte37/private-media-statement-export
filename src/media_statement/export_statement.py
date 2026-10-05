import argparse
import json
import os
from pathlib import Path

from .infrai_pdf import InfraiPdfClient
from .statement_exporter import StatementExporter
from .statement_models import AssetIngestion


def main() -> None:
    parser = argparse.ArgumentParser(description="Submit a media account statement PDF")
    parser.add_argument("input", type=Path, help="JSON asset ingestion file")
    args = parser.parse_args()
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        parser.error("INFRAI_API_KEY is required")
    asset = AssetIngestion.model_validate_json(args.input.read_text(encoding="utf-8"))
    delivery = StatementExporter(InfraiPdfClient(api_key)).submit(asset)
    print(json.dumps(delivery.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
