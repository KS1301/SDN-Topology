from ryu.lib.packet import arp


def handle_arp(controller, pkt, datapath, in_port):

    arp_pkt = pkt.get_protocol(arp.arp)

    if arp_pkt is None:
        return False

    controller.logger.info("=" * 50)
    controller.logger.info("ARP Packet Received")
    controller.logger.info("Source IP      : %s", arp_pkt.src_ip)
    controller.logger.info("Destination IP : %s", arp_pkt.dst_ip)
    controller.logger.info("Opcode         : %s", arp_pkt.opcode)
    controller.logger.info("=" * 50)

    controller.logger.info("ARP Packet Received")

    return False    