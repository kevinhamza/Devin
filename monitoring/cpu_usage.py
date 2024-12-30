"""
monitoring/cpu_usage.py
-----------------------
This module monitors CPU usage and provides real-time statistics for system performance
and analysis. It includes alerts, historical logging, and API support for external tools.
"""

import psutil
import time
from datetime import datetime
import logging
from flask import Flask, jsonify

# Constants
LOG_FILE = "monitoring/cpu_usage.log"
CPU_ALERT_THRESHOLD = 85  # Percentage

# Flask app for API
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def log_cpu_usage():
    """Logs current CPU usage to the log file."""
    usage = psutil.cpu_percent(interval=1)
    logging.info(f"CPU Usage: {usage}%")
    return usage

def check_alert_threshold(usage):
    """
    Checks if the CPU usage exceeds the threshold.
    Triggers an alert if the threshold is crossed.
    """
    if usage > CPU_ALERT_THRESHOLD:
        alert_message = f"ALERT: High CPU usage detected at {usage}%!"
        logging.warning(alert_message)
        print(alert_message)

@app.route('/api/cpu', methods=['GET'])
def get_cpu_usage():
    """
    API Endpoint: Returns the current CPU usage as JSON.
    """
    usage = psutil.cpu_percent(interval=1)
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "cpu_usage": usage
    })

def monitor_cpu(interval=5):
    """
    Monitors CPU usage at regular intervals.
    Args:
        interval (int): Time in seconds between checks.
    """
    try:
        while True:
            usage = log_cpu_usage()
            check_alert_threshold(usage)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("CPU monitoring stopped.")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CPU Usage Monitoring Tool")
    parser.add_argument('--api', action='store_true', help="Run API server")
    parser.add_argument('--interval', type=int, default=5, help="Monitoring interval in seconds")

    args = parser.parse_args()

    if args.api:
        print("Starting CPU Usage Monitoring API server...")
        app.run(host='0.0.0.0', port=5000)
    else:
        print(f"Starting CPU Usage Monitoring (Interval: {args.interval}s)...")
        monitor_cpu(interval=args.interval)
