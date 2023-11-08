"""
Your awesome Distance Vector router for CS 168

Based on skeleton code by:
  MurphyMc, zhangwen0411, lab352
"""

import sim.api as api
from cs168.dv import (
    RoutePacket,
    Table,
    TableEntry,
    DVRouterBase,
    Ports,
    FOREVER,
    INFINITY,
)


class DVRouter(DVRouterBase):

    # A route should time out after this interval
    ROUTE_TTL = 15

    # -----------------------------------------------
    # At most one of these should ever be on at once
    SPLIT_HORIZON = False
    POISON_REVERSE = True
    # -----------------------------------------------

    # Determines if you send poison for expired routes
    POISON_EXPIRED = True

    # Determines if you send updates when a link comes up
    SEND_ON_LINK_UP = False

    # Determines if you send poison when a link goes down
    POISON_ON_LINK_DOWN = False

    def __init__(self):
        """
        Called when the instance is initialized.
        DO NOT remove any existing code from this method.
        However, feel free to add to it for memory purposes in the final stage!
        """
        assert not (
            self.SPLIT_HORIZON and self.POISON_REVERSE
        ), "Split horizon and poison reverse can't both be on"

        self.start_timer()  # Starts signaling the timer at correct rate.

        # Contains all current ports and their latencies.
        # See the write-up for documentation.
        self.ports = Ports()

        # This is the table that contains all current routes
        self.table = Table()
        self.table.owner = self

    def add_static_route(self, host, port):
        """
        Adds a static route to this router's table.

        Called automatically by the framework whenever a host is connected
        to this router.

        :param host: the host.
        :param port: the port that the host is attached to.
        :returns: nothing.
        """
        # `port` should have been added to `peer_tables` by `handle_link_up`
        # when the link came up.
        assert port in self.ports.get_all_ports(), "Link should be up, but is not."

        # TODO: fill this in!
        self.table[host] = TableEntry(dst=host, port=port, latency=self.ports.get_latency(port), expire_time=FOREVER)

    def handle_data_packet(self, packet, in_port):
        """
        Called when a data packet arrives at this router.

        You may want to forward the packet, drop the packet, etc. here.

        :param packet: the packet that arrived.
        :param in_port: the port from which the packet arrived.
        :return: nothing.
        """
        # TODO: fill this in!
        if packet.dst in self.table.keys() and self.table[packet.dst].latency < INFINITY:
            self.send(packet=packet, port=self.table[packet.dst].port) # forward
        # drop

    def send_routes(self, force=False, single_port=None):
        """
        Send route advertisements for all routes in the table.

        :param force: if True, advertises ALL routes in the table;
                      otherwise, advertises only those routes that have
                      changed since the last advertisement.
               single_port: if not None, sends updates only to that port; to
                            be used in conjunction with handle_link_up.
        :return: nothing.
        """
        # TODO: fill this in!
        if force:
            for p in self.ports.get_all_ports():
                for k, v in self.table.items():
                    if self.SPLIT_HORIZON: 
                        if p != v.port:#  if this port is not the route's next hop
                            self.send_route(port=p, dst=k, latency=v.latency)
                        continue
                    elif self.POISON_REVERSE:
                        if p != v.port:
                            self.send_route(port=p, dst=k, latency=v.latency)
                        else: # if this port is next hop, send a INFINITY latency back (poison it)
                            self.send_route(port=p, dst=k, latency=INFINITY)
                        continue
                    else:
                        self.send_route(port=p, dst=k, latency=v.latency)

    def expire_routes(self):
        """
        Clears out expired routes from table.
        accordingly.
        """
        # TODO: fill this in!
        expire_host = []
        for k, v in self.table.items():
            if v.expire_time - api.current_time() <= 0:
                expire_host.append(k)
        for host in expire_host:
            if self.POISON_EXPIRED:
                dst, port = self.table[host].dst, self.table[host].port
                self.table[host] = TableEntry(dst=dst, port=port, latency=INFINITY, expire_time=self.ROUTE_TTL) # poisoning for a ttl
            else:
                del self.table[host]
            self.s_log(f"Router {self.name}'s route to {host.name} is expired")

    def handle_route_advertisement(self, route_dst, route_latency, port):
        """
        Called when the router receives a route advertisement from a neighbor.

        :param route_dst: the destination of the advertised route.
        :param route_latency: latency from the neighbor to the destination.
        :param port: the port that the advertisement arrived on.
        :return: nothing.
        """
        # TODO: fill this in!
        new_latency = route_latency + self.ports.get_latency(port)
        if new_latency > INFINITY: # don't exceed INFINITY!
            new_latency = INFINITY
        expire_time = self.ROUTE_TTL + api.current_time()
        if route_dst not in self.table.keys() or ( # route in path
                        ((self.table[route_dst].port == port and # same port, update route
                            not (new_latency >= INFINITY and self.table[route_dst].latency >= INFINITY)) or # don't charge timer
                        (new_latency < self.table[route_dst].latency and # new optimal route, break tie on choosing current route (spec erro)
                            new_latency < INFINITY)) # ignore new routes with latency INFINITY
                        ):
            self.table[route_dst] = TableEntry(dst=route_dst, 
                                                port=port, 
                                                latency=new_latency, 
                                                expire_time=expire_time)

    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this router goes up.

        :param port: the port that the link is attached to.
        :param latency: the link latency.
        :returns: nothing.
        """
        self.ports.add_port(port, latency)

        # TODO: fill in the rest!

    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this router goes down.

        :param port: the port number used by the link.
        :returns: nothing.
        """
        self.ports.remove_port(port)

        # TODO: fill this in!

    # Feel free to add any helper methods!
