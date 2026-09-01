from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel

from custom_topo import SDNTopology


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

    print("\nNetwork Nodes:")
    print("HTTP Clients : h1, h2, h3, h4, h5")
    print("Web Server   : server")
    print("Switches     : s1, s2")
    print("Controller   : Ryu")
    print("=" * 50)

    # Open Mininet CLI
    CLI(net)

    # Stop network
    net.stop()


if __name__ == '__main__':
    start_network()


    # from mininet.net import Mininet
# from mininet.node import RemoteController
# from mininet.cli import CLI
# from mininet.log import setLogLevel

# from custom_topo import SDNTopology
# setLogLevel('info')
# def start_network():

#     topo = SDNTopology()

#     controller = RemoteController(
#         'c0',
#         ip='127.0.0.1',
#         port=6653
#     )

#     net = Mininet(
#         topo=topo,
#          build=False,
#          autoSetMacs=True
#     )
#     # Add Remote Controller
#     net.addController(controller)
#     net.build()
#     # Start Mininet
#     net.start()

#         # Get Router
#     r1 = net.get('r1')

#     # Configure Router Interfaces
#     r1.cmd('ifconfig r1-eth0 10.0.1.1/24')
#     r1.cmd('ifconfig r1-eth1 10.0.2.1/24')

#     # Enable IP Forwarding
#     r1.cmd('sysctl -w net.ipv4.ip_forward=1')

#     # Get Hosts
#     h1 = net.get('h1')
#     h2 = net.get('h2')

#     # Configure Default Gateway 
#     h1.cmd('route add default gw 10.0.1.1')
#     h2.cmd('route add default gw 10.0.2.1')

#     print("=" * 50)
#     print("Network Started Successfully")
#     print("=" * 50)
#     # Open Mininet CLI
#     CLI(net)

#     # Stop Network
#     net.stop()
# if __name__ == '__main__':
#     start_network()

