
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel
from custom_topo import SDNTopology

import threading
import time
import csv
import os
from datetime import datetime

setLogLevel("info")


def start_network():
    topo = SDNTopology()

    controller = RemoteController(
        "c0", ip="127.0.0.1", port=6653
    )

    net = Mininet(
        topo=topo,
        build=False,
        autoSetMacs=True
    )

    net.addController(controller)
    net.build()
    net.start()

    print("\n" + "=" * 60)
    print("SDN NETWORK STARTED")
    print("=" * 60)

    hosts = [net.get(f"h{i}") for i in range(1, 6)]
    server = net.get("server")

    # Start the HTTP server only; no traffic starts automatically.
    server.cmd(
        "python3 -m http.server 80 "
        "> /tmp/http_server.log 2>&1 &"
    )
    time.sleep(1)

    server_check = server.cmd(
        "curl -s --connect-timeout 2 -o /dev/null "
        "-w '%{http_code}' http://10.0.0.10/"
    ).strip()

    if server_check != "200":
        print("WARNING: HTTP server check failed.")
        print("Check: server cat /tmp/http_server.log")
    else:
        print("HTTP server check: OK")

    results_dir = "/mnt/c/Kuldeep/SDN-Topology/results"
    os.makedirs(results_dir, exist_ok=True)

    # Shared progress data for the five client threads.
    progress = {
        host.name: {
            "completed": 0,
            "success": 0,
            "failure": 0
        }
        for host in hosts
    }

    progress_lock = threading.Lock()

    def generate_traffic(host, request_count, interval, experiment_dir):
        csv_path = os.path.join(
            experiment_dir, f"{host.name}_http.csv"
        )

        success = 0
        failure = 0

        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "elapsed_seconds",
                "host",
                "request_number",
                "http_status",
                "response_time_seconds",
                "response_bytes",
                "curl_exit_code",
                "success"
            ])

            for i in range(1, request_count + 1):
                timestamp = time.time()
                elapsed = timestamp - experiment_start

                result = host.cmd(
                    "curl -s "
                    "--connect-timeout 3 "
                    "--max-time 10 "
                    "-o /dev/null "
                    "-w '%{http_code},"
                    "%{time_total},"
                    "%{size_download}' "
                    "http://10.0.0.10/ "
                    "; printf ',%s' \"$?\""
                ).strip()

                parts = result.split(",")

                status = "000"
                response_time = -1.0
                response_bytes = 0
                exit_code = -1

                if len(parts) == 4:
                    try:
                        status = parts[0]
                        response_time = float(parts[1])
                        response_bytes = float(parts[2])
                        exit_code = int(parts[3])
                    except (ValueError, IndexError):
                        pass

                request_ok = status == "200" and exit_code == 0

                if request_ok:
                    success += 1
                else:
                    failure += 1

                writer.writerow([
                    timestamp,
                    elapsed,
                    host.name,
                    i,
                    status,
                    response_time,
                    response_bytes,
                    exit_code,
                    int(request_ok)
                ])
                f.flush()

                with progress_lock:
                    progress[host.name]["completed"] = i
                    progress[host.name]["success"] = success
                    progress[host.name]["failure"] = failure

                if i < request_count and interval > 0:
                    time.sleep(interval)

        print(
            f"\n[FINISHED] {host.name}: "
            f"success={success}, failure={failure}"
        )

    def show_progress(request_count, experiment_dir, stop_event):
        progress_path = os.path.join(
            experiment_dir, "progress.csv"
        )

        with open(progress_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "elapsed_seconds",
                "host",
                "completed",
                "total",
                "success",
                "failure",
                "progress_percent"
            ])

            while not stop_event.is_set():
                now = time.time()
                elapsed = now - experiment_start

                with progress_lock:
                    snapshot = {
                        name: values.copy()
                        for name, values in progress.items()
                    }

                total_done = sum(
                    item["completed"] for item in snapshot.values()
                )
                total_success = sum(
                    item["success"] for item in snapshot.values()
                )
                total_failure = sum(
                    item["failure"] for item in snapshot.values()
                )
                total_requests = len(hosts) * request_count
                percent = 100 * total_done / total_requests

                print("\n" + "-" * 60)
                print("LIVE HTTP EXPERIMENT PROGRESS")
                print(f"Overall: {total_done}/{total_requests} "
                      f"({percent:.2f}%)")
                print(f"Elapsed: {elapsed:.1f} seconds")
                print(
                    f"Success: {total_success} | "
                    f"Failed: {total_failure}"
                )

                for name, item in snapshot.items():
                    host_percent = (
                        100 * item["completed"] / request_count
                    )
                    print(
                        f"{name}: {item['completed']}/{request_count} "
                        f"({host_percent:.1f}%) | "
                        f"OK={item['success']} "
                        f"Failed={item['failure']}"
                    )

                    writer.writerow([
                        now, elapsed, name,
                        item["completed"], request_count,
                        item["success"], item["failure"],
                        host_percent
                    ])

                f.flush()
                print("-" * 60)

                stop_event.wait(2)

    def run_http_experiment(request_count=500, interval=1.0):
        global experiment_start

        experiment_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        experiment_dir = os.path.join(
            results_dir, f"http_{experiment_id}"
        )
        os.makedirs(experiment_dir, exist_ok=True)

        for host in hosts:
            with progress_lock:
                progress[host.name] = {
                    "completed": 0,
                    "success": 0,
                    "failure": 0
                }

        total_requests = len(hosts) * request_count

        print("\n" + "=" * 60)
        print("CONTROLLED HTTP LOAD TEST")
        print(f"Requests per host : {request_count}")
        print(f"Number of hosts   : {len(hosts)}")
        print(f"Total requests    : {total_requests}")
        print(f"Interval per host : {interval} seconds")
        print(f"Results directory : {experiment_dir}")
        print("Progress refresh  : every 2 seconds")
        print("=" * 60)

        experiment_start = time.time()
        stop_event = threading.Event()

        monitor = threading.Thread(
            target=show_progress,
            args=(request_count, experiment_dir, stop_event),
            daemon=True
        )
        monitor.start()

        threads = []
        try:
            for host in hosts:
                thread = threading.Thread(
                    target=generate_traffic,
                    args=(
                        host, request_count,
                        interval, experiment_dir
                    )
                )
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()
        finally:
            stop_event.set()
            monitor.join(timeout=3)

        duration = time.time() - experiment_start

        total_success = sum(
            item["success"] for item in progress.values()
        )
        total_failure = sum(
            item["failure"] for item in progress.values()
        )
        total_done = sum(
            item["completed"] for item in progress.values()
        )

        total_bytes = 0
        latency_values = []

        for host in hosts:
            csv_path = os.path.join(
                experiment_dir, f"{host.name}_http.csv"
            )

            with open(csv_path, newline="") as f:
                for row in csv.DictReader(f):
                    try:
                        total_bytes += float(row["response_bytes"])
                        if row["success"] == "1":
                            latency_values.append(
                                float(row["response_time_seconds"])
                            )
                    except (ValueError, KeyError):
                        pass

        request_rate = total_done / duration if duration > 0 else 0
        goodput_mbps = (
            total_bytes * 8 / duration / 1_000_000
            if duration > 0 else 0
        )
        average_latency_ms = (
            sum(latency_values) / len(latency_values) * 1000
            if latency_values else 0
        )

        summary_path = os.path.join(experiment_dir, "summary.csv")
        with open(summary_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "duration_seconds",
                "expected_requests",
                "completed_requests",
                "successful_requests",
                "failed_requests",
                "requests_per_second",
                "http_download_goodput_mbps",
                "average_success_latency_ms"
            ])
            writer.writerow([
                duration, total_requests, total_done,
                total_success, total_failure, request_rate,
                goodput_mbps, average_latency_ms
            ])

        print("\n" + "=" * 60)
        print("HTTP EXPERIMENT COMPLETED")
        print(f"Duration          : {duration:.2f} seconds")
        print(f"Expected requests : {total_requests}")
        print(f"Completed         : {total_done}")
        print(f"Successful        : {total_success}")
        print(f"Failed            : {total_failure}")
        print(f"Request rate      : {request_rate:.2f} req/s")
        print(f"HTTP goodput      : {goodput_mbps:.4f} Mbps")
        print(f"Average latency   : {average_latency_ms:.3f} ms")
        print(f"Results saved to  : {experiment_dir}")
        print("=" * 60)

    class ExperimentCLI(CLI):
        def do_http_test(self, line):
            """Usage: http_test [requests_per_host] [interval_seconds]"""

            args = line.split()
            try:
                count = int(args[0]) if len(args) >= 1 else 500
                interval = float(args[1]) if len(args) >= 2 else 1.0

                if count < 1 or interval < 0:
                    print("Use a positive request count and nonnegative interval.")
                    return

                run_http_experiment(count, interval)

            except ValueError:
                print("Usage: http_test [requests_per_host] [interval_seconds]")

    print("\nTraffic will NOT start automatically.")
    print("Default test: http_test 500 1")
    print("Type exit to stop Mininet.\n")

    try:
        ExperimentCLI(net)
    finally:
        net.stop()


if __name__ == "__main__":
    start_network()
