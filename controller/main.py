from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib import hub

from controller.s_handler import switch_features_handler as handle_switch
from controller.packet_handler import packet_in_handler as handle_packet
    

class MyController(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(MyController, self).__init__(*args, **kwargs)

        self.logger.info("=" * 50)
        self.logger.info("My Custom SDN Controller Started")
        self.logger.info("=" * 50)

        # MAC learning table
        self.mac_to_port = {}

        # Connected switches
        self.datapaths = {}

        # Start monitoring thread
        self.monitor_thread = hub.spawn(self._monitor)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):

        datapath = ev.msg.datapath

        # Store connected switch
        self.datapaths[datapath.id] = datapath

        handle_switch(self, ev)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):

        handle_packet(self, ev)

    # -----------------------------
    # Traffic Monitoring
    # -----------------------------

    def _monitor(self):

        while True:

            for datapath in self.datapaths.values():

                self._request_stats(datapath)

            hub.sleep(5)

    def _request_stats(self, datapath):

        parser = datapath.ofproto_parser

        # Request flow statistics
        req = parser.OFPFlowStatsRequest(datapath)

        datapath.send_msg(req)

    # -----------------------------
    # Receive Flow Statistics
    # -----------------------------

    # @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    # def flow_stats_reply_handler(self, ev):

    #     datapath = ev.msg.datapath

    #     dpid = datapath.id

    #     self.logger.info("=" * 50)
    #     self.logger.info("TRAFFIC MONITORING")
    #     self.logger.info("Switch DPID : %016x", dpid)

    #     for stat in ev.msg.body:

    #         self.logger.info(
    #             "Packets : %d | Bytes : %d | Priority : %d",
    #             stat.packet_count,
    #             stat.byte_count,
    #             stat.priority
    #         )

    #     self.logger.info("=" * 50)
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):

        datapath = ev.msg.datapath
        dpid = datapath.id

        total_packets = 0
        total_bytes = 0
        flow_count = 0

        for stat in ev.msg.body:

            # Ignore table-miss rule
            if stat.priority == 0:
                continue

            flow_count += 1
            total_packets += stat.packet_count
            total_bytes += stat.byte_count

        self.logger.info("=" * 50)
        self.logger.info("TRAFFIC MONITORING - SWITCH %s", dpid)
        self.logger.info("=" * 50)

        self.logger.info("Flow Count    : %d", flow_count)
        self.logger.info("Total Packets : %d", total_packets)
        self.logger.info("Total Bytes   : %d", total_bytes)

        self.logger.info("=" * 50)