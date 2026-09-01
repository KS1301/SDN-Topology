def add_flow(datapath, priority, match, actions,
             idle_timeout=0, hard_timeout=0):

    ofproto = datapath.ofproto
    parser = datapath.ofproto_parser

    inst = [
        parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS,
            actions
        )
    ]

    mod = parser.OFPFlowMod(
        datapath=datapath,
        priority=priority,
        match=match,
        instructions=inst,
        idle_timeout=idle_timeout,
        hard_timeout=hard_timeout
    )

    datapath.send_msg(mod)