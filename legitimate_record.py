import time
from mininet.net import Mininet
from mininet.node import RemoteController

DURATION = 60          # seconds
REQUESTS_PER_SEC = 1   # per host

HOSTS = ["h1", "h2", "h3", "h4", "h5"]

def generate_traffic(net):
    print("\n=== LEGITIMATE TRAFFIC STARTED ===")
    print(f"Duration: {DURATION} seconds")
    print(f"Rate: {REQUESTS_PER_SEC} request/sec/host")
    print(f"Hosts: {len(HOSTS)}")
    print(
        f"Expected HTTP requests: "
        f"{len(HOSTS) * REQUESTS_PER_SEC * DURATION}"
    )
    print("===================================\n")

    end_time = time.time() + DURATION
    request_count = {h: 0 for h in HOSTS}

    while time.time() < end_time:

        start = time.time()

        for host_name in HOSTS:
            host = net.get(host_name)

            host.cmd(
                "curl -s --connect-timeout 2 "
                "http://10.0.0.10/ > /dev/null"
            )

            request_count[host_name] += 1

        elapsed = time.time() - start

        sleep_time = max(0, 1 / REQUESTS_PER_SEC - elapsed)

        time.sleep(sleep_time)

    print("\n=== TRAFFIC COMPLETED ===")

    total = sum(request_count.values())

    for host, count in request_count.items():
        print(f"{host}: {count} requests")

    print(f"Total generated requests: {total}")


if __name__ == "__main__":
    print("This script should be executed with an existing Mininet network.")