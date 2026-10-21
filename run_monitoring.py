"""Run drift and performance monitoring over the three incoming batches.

Writes a combined JSON report and a Markdown summary into the results
directory. This is the evidence for Task 7: it shows which batches breach the
drift and performance thresholds and why.
"""
import json
import logging
import os

import pandas as pd

from src.config_loader import load_config
from src.pipeline import monitoring_flow

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("monitoring")


def main() -> None:
    config = load_config("config/config.yaml")
    incoming = pd.read_csv(config["data"]["incoming_batches_path"])
    results_dir = config["data"]["results_dir"]
    os.makedirs(results_dir, exist_ok=True)

    results = []
    for batch in sorted(incoming["Batch"].unique()):
        batch_df = incoming[incoming["Batch"] == batch].copy()
        logger.info("Monitoring batch %s", batch)
        results.append(monitoring_flow(batch_df, "config/config.yaml", batch_label=f"batch_{batch}"))

    json_path = os.path.join(results_dir, "monitoring_report.json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    md_path = os.path.join(results_dir, "monitoring_report.md")
    with open(md_path, "w") as f:
        f.write("# Monitoring report: incoming batches\n\n")
        f.write("| Batch | Rows | Drifted features | Watch | Batch RMSE | Ref RMSE | Alert |\n")
        f.write("|-------|------|------------------|-------|-----------|----------|-------|\n")
        for r in results:
            if r.get("status") == "rejected":
                f.write(f"| {r['batch']} | - | data gate rejected | - | - | - | yes |\n")
                continue
            f.write(
                f"| {r['batch']} | {r['n_rows']} | "
                f"{', '.join(r['drifted_features']) or 'none'} | "
                f"{', '.join(r['watch_features']) or 'none'} | "
                f"{r.get('batch_rmse', '-')} | {r.get('reference_rmse', '-')} | "
                f"{'yes' if r.get('alert') else 'no'} |\n"
            )
    logger.info("Wrote %s and %s", json_path, md_path)
    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
