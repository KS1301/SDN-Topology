from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel

from custom_topo import SDNTopology

import threading
import time

setLogLevel('info')


def start_network():

    # Create topology
    topo = SDNTopology()

    # Connect to Ryu Controller
    controller = RemoteController(
        'c0',
        ip='127.0.0.1',
        port=6653
    )

    # Create Mininet network
    net = Mininet(
        topo=topo,
        build=False,
        autoSetMacs=True
    )

    # Add Remote Controller
    net.addController(controller)

    # Build network
    net.build()

    # Start network
    net.start()

    print("=" * 50)
    print("SDN Network Started Successfully")
    print("=" * 50)

    # Get hosts
    h1 = net.get('h1')
    h2 = net.get('h2')
    h3 = net.get('h3')
    h4 = net.get('h4')
    h5 = net.get('h5')
    server = net.get('server')

    server.cmd('python3 -m http.server 80 > /tmp/http_server.log 2>&1 &')
    print("\nNetwork Nodes:")
    print("HTTP Clients : h1, h2, h3, h4, h5")
    print("Web Server   : server")
    print("Switches     : s1, s2")
    print("Controller   : Ryu")
    print("=" * 50)

    # ==================================================
    # LEGITIMATE TRAFFIC GENERATOR
    # ==================================================

    def generate_traffic(host, duration=60, interval=1):

        start_time = time.time()
        count = 0

        while time.time() - start_time < duration:

            host.cmd(
                'curl -s --connect-timeout 2 '
                'http://10.0.0.10/ > /dev/null'
            )

            count += 1

            elapsed = time.time() - start_time
            next_time = count * interval

            sleep_time = next_time - elapsed

            if sleep_time > 0:
                time.sleep(sleep_time)

        print(
            f"[TRAFFIC] {host.name} completed "
            f"{count} HTTP requests"
        )

    # ==================================================
    # START LEGITIMATE TRAFFIC
    # ==================================================

    duration = 60
    request_rate = 1

    print("\n" + "=" * 50)
    print("LEGITIMATE TRAFFIC EXPERIMENT")
    print("=" * 50)
    print("Duration             : 60 seconds")
    print("Request rate/host    : 1 request/sec")
    print("Number of hosts      : 5")
    print("Expected requests    : 300")
    print("=" * 50)

    hosts = [h1, h2, h3, h4, h5]

    threads = []

    experiment_start = time.time()

    # Start H1-H5 simultaneously
    for host in hosts:

        thread = threading.Thread(
            target=generate_traffic,
            args=(host, duration, 1)
        )

        thread.start()
        threads.append(thread)

    # Wait for all hosts to finish
    for thread in threads:
        thread.join()

    experiment_end = time.time()

    actual_duration = experiment_end - experiment_start

    print("\n" + "=" * 50)
    print("LEGITIMATE TRAFFIC EXPERIMENT COMPLETED")
    print("=" * 50)
    print(
        f"Actual experiment duration : "
        f"{actual_duration:.2f} seconds"
    )
    print("Expected HTTP requests     : 300")
    print("=" * 50)

    # ==================================================
    # OPEN MININET CLI
    # ==================================================

    CLI(net)

    # Stop network
    net.stop()


if __name__ == '__main__':
    start_network()