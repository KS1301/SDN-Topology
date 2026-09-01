import time

from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import tcp

from controller.mac_learning import learn_mac
from controller.mac_learning import get_output_port
from controller.flow_manager import add_flow
from controller.arp_handler import handle_arp


def packet_in_handler(controller, ev):

    msg = ev.msg
    datapath = msg.datapath
    in_port = msg.match['in_port']

    flow_start_time = time.perf_counter()
    controller_start_time = time.perf_counter()

    pkt = packet.Packet(msg.data)
    eth = pkt.get_protocol(ethernet.ethernet)

    # -----------------------------------------
    # Handle ARP
    # -----------------------------------------

    if handle_arp(controller, pkt, datapath, in_port):
        return

    if eth is None:
        return

    src = eth.src
    dst = eth.dst
    dpid = datapath.id

    # -----------------------------------------
    # Ignore IPv6 multicast background traffic
    # -----------------------------------------

    if dst.startswith("33:33:"):
        return

    # -----------------------------------------
    # MAC Learning
    # -----------------------------------------

    learn_mac(
        controller,
        dpid,
        src,
        in_port
    )

    parser = datapath.ofproto_parser
    ofproto = datapath.ofproto

    # -----------------------------------------
    # Find destination port
    # -----------------------------------------

    out_port = get_output_port(
        controller,
        dpid,
        dst,
        ofproto
    )

    # -----------------------------------------
    # Packet information
    # -----------------------------------------

    controller.logger.info(
        "[PACKET] S%d | %s -> %s | IN=%s",
        dpid,
        src,
        dst,
        in_port
    )

    # -----------------------------------------
    # Detect IPv4/TCP
    # -----------------------------------------

    ip_pkt = pkt.get_protocol(ipv4.ipv4)
    tcp_pkt = pkt.get_protocol(tcp.tcp)

    if ip_pkt and tcp_pkt:

        controller.logger.info(
            "[TCP] %s:%s -> %s:%s",
            ip_pkt.src,
            tcp_pkt.src_port,
            ip_pkt.dst,
            tcp_pkt.dst_port
        )

        # HTTP uses TCP port 80
        if tcp_pkt.dst_port == 80 or tcp_pkt.src_port == 80:

            controller.logger.info(
                "[HTTP] Client=%s:%s -> Server=%s:%s",
                ip_pkt.src,
                tcp_pkt.src_port,
                ip_pkt.dst,
                tcp_pkt.dst_port
            )

    # -----------------------------------------
    # Forwarding decision
    # -----------------------------------------

    if out_port == ofproto.OFPP_FLOOD:

        controller.logger.info(
            "[FORWARD] S%d | UNKNOWN -> FLOOD",
            dpid
        )

    else:

        controller.logger.info(
            "[FORWARD] S%d | KNOWN -> OUT=%s",
            dpid,
            out_port
        )

    actions = [
        parser.OFPActionOutput(out_port)
    ]

    # -----------------------------------------
    # Install flow if destination is known
    # -----------------------------------------

    if out_port != ofproto.OFPP_FLOOD:

        match = parser.OFPMatch(
            in_port=in_port,
            eth_src=src,
            eth_dst=dst
        )

        add_flow(
            datapath,
            priority=1,
            match=match,
            actions=actions,
            idle_timeout=30,
            hard_timeout=60
        )

        flow_setup_time = (
            time.perf_counter() - flow_start_time
        ) * 1000

        controller.logger.info(
            "[FLOW] S%d | INSTALLED | Setup=%.3f ms",
            dpid,
            flow_setup_time
        )

    # -----------------------------------------
    # Send Packet-Out
    # -----------------------------------------

    out = parser.OFPPacketOut(
        datapath=datapath,
        buffer_id=msg.buffer_id,
        in_port=in_port,
        actions=actions,
        data=msg.data
    )

    datapath.send_msg(out)

    # -----------------------------------------
    # Controller response time
    # -----------------------------------------

    controller_response_time = (
        time.perf_counter() - controller_start_time
    ) * 1000

    controller.logger.info(
        "[CONTROLLER] S%d | Response=%.3f ms",
        dpid,
        controller_response_time
    )