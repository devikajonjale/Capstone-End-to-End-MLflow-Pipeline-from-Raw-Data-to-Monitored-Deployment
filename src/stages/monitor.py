import os
import logging
from prefect import task
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, TargetDriftPreset
from src.config_loader import load_config

logger = logging.getLogger(__name__)

@task
def monitor_batch(batch_df, reference_df, config_path='config/config.yaml'):
    """Use Evidently to compute data drift report."""
    config = load_config(config_path)
    monitor_config = config.get('monitoring', {})
    
    logger.info("Generating evidently drift report...")
    
    report = Report(metrics=[
        DataDriftPreset(),
        TargetDriftPreset()
    ])
    
    report.run(reference_data=reference_df, current_data=batch_df)
    
    artifacts_dir = "artifacts/monitoring"
    os.makedirs(artifacts_dir, exist_ok=True)
    report_path = os.path.join(artifacts_dir, "drift_report.html")
    
    report.save_html(report_path)
    logger.info(f"Saved drift report to {report_path}")
    
    drift_result = report.as_dict()
    dataset_drift = drift_result.get('metrics', [])[0].get('result', {}).get('dataset_drift', False)
    
    if dataset_drift:
        logger.warning("DATA DRIFT DETECTED!")
    else:
        logger.info("No significant data drift detected.")
        
    return drift_result
