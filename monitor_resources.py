import csv
import os
import time
import psutil
from datetime import datetime

# Store resource monitoring data in the project results folder
RESULTS_DIR = "results"
os.makedirs(RESULTS_DIR, exist_ok=True)

# Create a unique CSV file for each monitoring session
filename = os.path.join(
    RESULTS_DIR,
    f"resource_usage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
)

with open(filename, "w", newline="") as f:
    writer = csv.writer(f)

    writer.writerow([
        "timestamp",
        "elapsed_seconds",
        "cpu_percent",
        "memory_percent",
        "memory_used_mb"
    ])

    start = time.time()

    print("CPU and RAM monitoring started.")
    print(f"Output CSV: {filename}")
    print("Press Ctrl+C to stop monitoring.")

    try:
        while True:
            # Measure CPU utilization over a one-second interval
            cpu = psutil.cpu_percent(interval=1)

            # Measure system memory
            memory = psutil.virtual_memory()

            timestamp = time.time()
            elapsed = round(timestamp - start, 2)
            memory_used_mb = round(
                memory.used / (1024 * 1024), 2
            )

            writer.writerow([
                timestamp,
                elapsed,
                cpu,
                memory.percent,
                memory_used_mb
            ])

            # Save every sample immediately
            f.flush()

            print(
                f"CPU: {cpu:.1f}% | "
                f"RAM: {memory.percent:.1f}% | "
                f"Used: {memory_used_mb:.0f} MB"
            )

    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
        print(f"Data saved to: {filename}")