from mininet.topo import Topo


class SDNTopology(Topo):

    def build(self):

        # Client
        h1 = self.addHost(
            'h1',
            ip='10.0.1.2/24'
        )

        # Server
        h2 = self.addHost(
            'h2',
            ip='10.0.2.2/24'
        )

        # Router
        r1 = self.addHost(
            'r1',
            ip=None
        )

        # OpenFlow Switch 1
        s1 = self.addSwitch(
            's1',
            protocols='OpenFlow13'
        )

        # OpenFlow Switch 2
        s2 = self.addSwitch(
            's2',
            protocols='OpenFlow13'
        )

        # Links
        self.addLink(h1, s1)
        self.addLink(s1, r1)
        self.addLink(r1, s2)
        self.addLink(s2, h2)


topos = {
    'sdntopo': SDNTopology
}