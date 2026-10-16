
import csv
import time
from pathlib import Path

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import (
    CONFIG_DISPATCHER,
    MAIN_DISPATCHER,
    set_ev_cls,
)
from ryu.ofproto import ofproto_v1_3
from ryu.lib import hub

from controller.s_handler import switch_features_handler as handle_switch
from controller.packet_handler import packet_in_handler as handle_packet


RESULTS_DIR = Path("results")


class MyController(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(MyController, self).__init__(*args, **kwargs)

        RESULTS_DIR.mkdir(parents=True, exist_ok=True)

        self.logger.info("=" * 50)
        self.logger.info("My Custom SDN Controller Started")
        self.logger.info("=" * 50)

        self.mac_to_port = {}
        self.datapaths = {}

        # Measurement counters
        self.packet_in_count = 0
        self.flow_mod_requests = 0
        self.packet_in_time_ms_total = 0.0

        self.stats_file = RESULTS_DIR / "switch_stats.csv"

        if not self.stats_file.exists():
            with self.stats_file.open("w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "switch_dpid",
                    "flow_count",
                    "total_packets",
                    "total_bytes",
                ])

        self.monitor_thread = hub.spawn(self._monitor)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        self.datapaths[datapath.id] = datapath
        handle_switch(self, ev)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        self.packet_in_count += 1
        started = time.perf_counter()

        try:
            handle_packet(self, ev)
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000
            self.packet_in_time_ms_total += elapsed_ms

    def _monitor(self):
        while True:
            for datapath in list(self.datapaths.values()):
                self._request_stats(datapath)

            hub.sleep(5)

    def _request_stats(self, datapath):
        parser = datapath.ofproto_parser
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):
        datapath = ev.msg.datapath
        dpid = datapath.id

        total_packets = 0
        total_bytes = 0
        flow_count = 0

        for stat in ev.msg.body:

            flow_count += 1
            total_packets += stat.packet_count
            total_bytes += stat.byte_count

        timestamp = time.time()

        with self.stats_file.open("a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                dpid,
                flow_count,
                total_packets,
                total_bytes,
            ])

        self.logger.info(
            "STATS switch=%s flows=%d packets=%d bytes=%d "
            "packet_in_total=%d flow_mod_requests=%d "
            "packet_in_time_ms_total=%.3f",
            dpid,
            flow_count,
            total_packets,
            total_bytes,
            self.packet_in_count,
            self.flow_mod_requests,
            self.packet_in_time_ms_total,
        )
