"""
monitoring/analytics_dashboard.py

This module provides functionalities for generating, managing, and displaying analytics data
in a dashboard format. It integrates real-time data visualization for system performance and
user-specific metrics.
"""

import os
import psutil
import platform
import time
import matplotlib.pyplot as plt
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Function to collect system analytics
def collect_system_metrics():
    """Collect system metrics such as CPU, memory, and disk usage."""
    metrics = {
        "cpu_usage": psutil.cpu_percent(interval=1),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "uptime": time.time() - psutil.boot_time(),
        "os": platform.system(),
        "os_version": platform.version(),
        "hostname": platform.node(),
    }
    return metrics

# Endpoint to fetch analytics data
@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """API endpoint to fetch system metrics."""
    metrics = collect_system_metrics()
    return jsonify(metrics)

# Main dashboard route
@app.route('/')
def dashboard():
    """Render the main analytics dashboard."""
    return render_template('dashboard.html')

# Function to generate visualizations
def generate_visualizations():
    """Generate real-time visualizations for system analytics."""
    metrics = collect_system_metrics()

    # Create CPU usage pie chart
    cpu_usage = metrics["cpu_usage"]
    plt.figure(figsize=(6, 4))
    plt.pie(
        [cpu_usage, 100 - cpu_usage],
        labels=["Used", "Available"],
        autopct="%1.1f%%",
        colors=["red", "green"],
    )
    plt.title("CPU Usage")
    plt.savefig("static/cpu_usage.png")
    plt.close()

    # Create memory usage bar chart
    memory_usage = metrics["memory_usage"]
    plt.figure(figsize=(6, 4))
    plt.bar(["Memory Used", "Memory Available"], [memory_usage, 100 - memory_usage], color="blue")
    plt.title("Memory Usage")
    plt.savefig("static/memory_usage.png")
    plt.close()

    # Disk usage
    disk_usage = metrics["disk_usage"]
    plt.figure(figsize=(6, 4))
    plt.pie(
        [disk_usage, 100 - disk_usage],
        labels=["Used", "Available"],
        autopct="%1.1f%%",
        colors=["purple", "yellow"],
    )
    plt.title("Disk Usage")
    plt.savefig("static/disk_usage.png")
    plt.close()

# Periodically update visualizations
def periodic_visualization_updates(interval=30):
    """Update visualizations periodically."""
    while True:
        generate_visualizations()
        time.sleep(interval)

# Main function to run the Flask app
if __name__ == '__main__':
    # Ensure the static directory exists
    os.makedirs("static", exist_ok=True)

    # Generate initial visualizations
    generate_visualizations()

    # Start the Flask application
    app.run(host='0.0.0.0', port=8080, debug=True)
