from controller.flow_manager import add_flow


def switch_features_handler(controller, ev):
    datapath = ev.msg.datapath
    ofproto = datapath.ofproto
    parser = datapath.ofproto_parser

    controller.logger.info("=" * 50)
    controller.logger.info("Switch Connected")
    controller.logger.info("DPID : %016x", datapath.id)
    controller.logger.info("=" * 50)

    match = parser.OFPMatch()

    actions = [
        parser.OFPActionOutput(
            ofproto.OFPP_CONTROLLER,
            ofproto.OFPCML_NO_BUFFER
        )
    ]

    add_flow(datapath, 0, match, actions)

    controller.logger.info("Table-Miss Flow Installed Successfully")