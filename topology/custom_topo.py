
from mininet.topo import Topo
from mininet.link import TCLink


class SDNTopology(Topo):

    def build(self):

        # =========================
        # HTTP CLIENTS
        # =========================

        h1 = self.addHost('h1', ip='10.0.0.1/24')
        h2 = self.addHost('h2', ip='10.0.0.2/24')
        h3 = self.addHost('h3', ip='10.0.0.3/24')
        h4 = self.addHost('h4', ip='10.0.0.4/24')
        h5 = self.addHost('h5', ip='10.0.0.5/24')

        # =========================
        # HTTP SERVER
        # =========================

        server = self.addHost(
            'server',
            ip='10.0.1.10/24'
        )

        # =========================
        # LINUX ROUTER
        # IPs will be configured in run_topo.py
        # =========================

        r1 = self.addHost('r1', ip=None)

        # =========================
        # OPENFLOW SWITCHES
        # =========================

        s1 = self.addSwitch(
            's1',
            protocols='OpenFlow13'
        )

        s2 = self.addSwitch(
            's2',
            protocols='OpenFlow13'
        )

        # =========================
        # CLIENTS -> S1
        # Bandwidth: 100 Mbps
        # =========================

        for host in [h1, h2, h3, h4, h5]:
            self.addLink(
                host, s1,
                cls=TCLink,
                bw=100
            )

        # =========================
        # S1 -> S2
        # Bandwidth: 100 Mbps
        # =========================

        self.addLink(
            s1, s2,
            cls=TCLink,
            bw=100
        )

        # =========================
        # S2 -> ROUTER
        # Bottleneck: 10 Mbps
        # =========================

        self.addLink(
            s2, r1,
            cls=TCLink,
            bw=10
        )

        # =========================
        # ROUTER -> SERVER
        # Bandwidth: 100 Mbps
        # =========================

        self.addLink(
            r1, server,
            cls=TCLink,
            bw=100
        )


topos = {
    'sdntopo': SDNTopology
}
