
import csv
from pathlib import Path
import matplotlib.pyplot as plt

ROOT = Path("results")
TESTS = {
    "Test 1 (1s)": ROOT / "http_20261012_051840",
    "Test 2 (0.2s)": ROOT / "http_20261012_052922",
}
OUT = ROOT / "graphs"
OUT.mkdir(parents=True, exist_ok=True)


def read_csv(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


# Load actual experiment summaries
data = {}
for name, folder in TESTS.items():
    rows = read_csv(folder / "summary.csv")
    if not rows:
        raise ValueError(f"No data in {folder / 'summary.csv'}")

    row = rows[0]
    data[name] = {
        "rate": float(row["requests_per_second"]),
        "latency": float(row["average_success_latency_ms"]),
        "success": int(row["successful_requests"]),
        "failed": int(row["failed_requests"]),
        "goodput": float(row["http_download_goodput_mbps"]),
    }


def save_bar(filename, title, ylabel, key):
    plt.figure(figsize=(8, 5))
    plt.bar(list(data), [v[key] for v in data.values()])
    plt.title(title)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(OUT / filename, dpi=160)
    plt.close()


# 1. Request rate
save_bar(
    "request_rate.png",
    "HTTP Request Rate",
    "Requests per second",
    "rate",
)

# 2. Average successful-request latency
save_bar(
    "average_latency.png",
    "Average HTTP Response Latency",
    "Milliseconds",
    "latency",
)

# 3. HTTP response-body goodput (not total network throughput)
save_bar(
    "http_goodput.png",
    "HTTP Response-Body Goodput",
    "Mbps",
    "goodput",
)

# 4. Successful and failed HTTP requests
names = list(data)
x = list(range(len(names)))
width = 0.35

plt.figure(figsize=(8, 5))
plt.bar(
    [i - width / 2 for i in x],
    [data[n]["success"] for n in names],
    width,
    label="Successful",
)
plt.bar(
    [i + width / 2 for i in x],
    [data[n]["failed"] for n in names],
    width,
    label="Failed",
)
plt.xticks(x, names)
plt.ylabel("Requests")
plt.title("HTTP Request Outcomes")
plt.legend()
plt.tight_layout()
plt.savefig(OUT / "request_outcomes.png", dpi=160)
plt.close()

# 5. Per-host response-time distributions from request CSVs
for name, folder in TESTS.items():
    labels = []
    values = []

    for i in range(1, 6):
        rows = read_csv(folder / f"h{i}_http.csv")
        latencies = [
            float(row["response_time_seconds"]) * 1000
            for row in rows
            if row.get("success") == "1"
            and float(row["response_time_seconds"]) >= 0
        ]
        labels.append(f"h{i}")
        values.append(latencies)

    plt.figure(figsize=(8, 5))
    plt.boxplot(values, tick_labels=labels)
    plt.ylabel("Response time (ms)")
    plt.xlabel("Client host")
    plt.title(f"Per-Host HTTP Latency — {name}")
    plt.tight_layout()

    filename = (
        "test1_host_latency.png"
        if name.startswith("Test 1")
        else "test2_host_latency.png"
    )
    plt.savefig(OUT / filename, dpi=160)
    plt.close()

# 6–8. Recorded switch statistics
switch_file = ROOT / "switch_stats.csv"

if switch_file.exists():
    rows = read_csv(switch_file)

    if rows:
        start = min(float(r["timestamp"]) for r in rows)

        graphs = [
            (
                "total_packets",
                "Recorded packet counter",
                "switch_packets.png",
                "Switch Packet Counters",
            ),
            (
                "total_bytes",
                "Recorded byte counter",
                "switch_bytes.png",
                "Switch Byte Counters",
            ),
            (
                "flow_count",
                "Flow count",
                "switch_flows.png",
                "Switch Flow Count",
            ),
        ]

        for column, ylabel, filename, title in graphs:
            plt.figure(figsize=(9, 5))

            for dpid in sorted(set(r["switch_dpid"] for r in rows)):
                points = sorted(
                    (
                        float(r["timestamp"]) - start,
                        float(r[column]),
                    )
                    for r in rows
                    if r["switch_dpid"] == dpid
                )

                plt.plot(
                    [p[0] for p in points],
                    [p[1] for p in points],
                    label=f"Switch {dpid}",
                )

            plt.xlabel("Seconds since first recorded sample")
            plt.ylabel(ylabel)
            plt.title(title)
            plt.legend()
            plt.tight_layout()
            plt.savefig(OUT / filename, dpi=160)
            plt.close()

print(f"\nGraphs saved in: {OUT.resolve()}")
for path in sorted(OUT.glob("*.png")):
    print(path.name)
