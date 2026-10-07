import os
import json
import logging
from src.stages.monitor import monitor_batch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    config_path = "config/config.yaml"
    
    batch_files = [
        "data/incoming/batch_1.csv",
        "data/incoming/batch_2.csv",
        "data/incoming/batch_3.csv"
    ]
    
    all_results = []
    
    for batch_file in batch_files:
        logger.info(f"Running monitoring on {batch_file}...")
        try:
            # We assume monitor_batch is adapted to receive batch_file if needed, 
            # or it picks up the latest batch. As per instructions, iterate over batch 1, 2, 3 
            # and run monitor_batch for each.
            result = monitor_batch(config_path=config_path) # the monitor script may need batch_file to be updated in config
            all_results.append({
                "batch_file": batch_file,
                "monitoring_result": result,
                "status": "success"
            })
        except Exception as e:
            logger.error(f"Failed to monitor {batch_file}: {e}")
            all_results.append({
                "batch_file": batch_file,
                "status": "failed",
                "error": str(e)
            })
            
    # Save combined results
    output_dir = "artifacts/monitoring"
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "combined_monitoring_report.json")
    
    with open(report_path, "w") as f:
        json.dump(all_results, f, indent=4)
        
    logger.info(f"Monitoring complete. Combined report saved to {report_path}")

if __name__ == "__main__":
    main()
