import time
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
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
    # Handle ARP Packet

    if handle_arp(controller, pkt, datapath, in_port):
        return

    if eth is None:
        return


    src = eth.src
    dst = eth.dst

    dpid = datapath.id

    learn_mac(controller, dpid, src, in_port)

    parser = datapath.ofproto_parser
    ofproto = datapath.ofproto

    out_port = get_output_port(
    controller,
    dpid,
    dst,
    ofproto
    )   

    actions = [parser.OFPActionOutput(out_port)]
    # Install flow if destination is known
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

        flow_setup_time = (time.perf_counter() - flow_start_time) * 1000

        controller.logger.info("Flow Installed Successfully")
        controller.logger.info(
            "Flow Setup Time : %.3f ms",
            flow_setup_time
        )

    out = parser.OFPPacketOut(
        datapath=datapath,
        buffer_id=msg.buffer_id,
        in_port=in_port,
        actions=actions,
        data=msg.data
    )

    datapath.send_msg(out)
    controller_response_time = (
        time.perf_counter() - controller_start_time
    ) * 1000

    controller.logger.info(
        "Controller Response Time : %.3f ms",
        controller_response_time
    )
    controller.logger.info("=" * 50)
    controller.logger.info("Packet Received")
    controller.logger.info("Switch DPID : %016x", datapath.id)
    controller.logger.info("Source MAC  : %s", src)
    controller.logger.info("Destination : %s", dst)
    controller.logger.info("Input Port  : %s", in_port)
    controller.logger.info("=" * 50)