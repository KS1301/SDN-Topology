def learn_mac(controller, dpid, src, in_port):
    """
    Learn Source MAC Address
    """

    if dpid not in controller.mac_to_port:
        controller.mac_to_port[dpid] = {}

    controller.mac_to_port[dpid][src] = in_port

    controller.logger.info(
        "MAC Learned: Switch=%s  MAC=%s  Port=%s",
        dpid,
        src,
        in_port
    )


def get_output_port(controller, dpid, dst, ofproto):
    """
    Return output port if destination MAC is known.
    Otherwise return FLOOD.
    """

    if dpid in controller.mac_to_port:

        if dst in controller.mac_to_port[dpid]:
            return controller.mac_to_port[dpid][dst]

    return ofproto.OFPP_FLOOD