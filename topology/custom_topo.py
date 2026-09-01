from mininet.topo import Topo


class SDNTopology(Topo):

    def build(self):

        # =========================
        # HTTP CLIENTS
        # =========================

        h1 = self.addHost(
            'h1',
            ip='10.0.0.1/24'
        )

        h2 = self.addHost(
            'h2',
            ip='10.0.0.2/24'
        )

        h3 = self.addHost(
            'h3',
            ip='10.0.0.3/24'
        )

        h4 = self.addHost(
            'h4',
            ip='10.0.0.4/24'
        )

        h5 = self.addHost(
            'h5',
            ip='10.0.0.5/24'
        )

        # =========================
        # WEB SERVER
        # =========================

        server = self.addHost(
            'server',
            ip='10.0.0.10/24'
        )

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
        # CLIENTS → SWITCH 1
        # =========================

        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s1)
        self.addLink(h4, s1)
        self.addLink(h5, s1)

        # =========================
        # SWITCH 1 → SWITCH 2
        # =========================

        self.addLink(s1, s2)

        # =========================
        # SWITCH 2 → WEB SERVER
        # =========================

        self.addLink(s2, server)


topos = {
    'sdntopo': SDNTopology
}


# from mininet.topo import Topo


# class SDNTopology(Topo):

#     def build(self):

#         # Client
#         h1 = self.addHost(
#             'h1',
#             ip='10.0.1.2/24'
#         )

#         # Server
#         h2 = self.addHost(
#             'h2',
#             ip='10.0.2.2/24'
#         )

#         # Router
#         r1 = self.addHost(
#             'r1',
#             ip=None
#         )

#         # OpenFlow Switch 1
#         s1 = self.addSwitch(
#             's1',
#             protocols='OpenFlow13'
#         )

#         # OpenFlow Switch 2
#         s2 = self.addSwitch(
#             's2',
#             protocols='OpenFlow13'
#         )

#         # Links
#         self.addLink(h1, s1)
#         self.addLink(s1, r1)
#         self.addLink(r1, s2)
#         self.addLink(s2, h2)


# topos = {
#     'sdntopo': SDNTopology
# }

