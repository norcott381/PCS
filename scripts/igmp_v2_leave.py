#!/usr/bin/env python

from pcs.packets.localhost import *
from pcs.packets.ethernet import *
from pcs.packets.ipv4 import *
from pcs.packets.igmpv2 import *
from pcs.packets.payload import *
from pcs import *
from time import sleep

# Spoof an IGMPv2 HOST LEAVE message.

def main():

    from optparse import OptionParser
    
    parser = OptionParser()

    parser.add_option("-I", "--ether_iface",
                      dest="ether_iface", default=None,
                      help="The name of the source interface.")

    parser.add_option("-e", "--ether_source",
                      dest="ether_source", default=None,
                      help="The host Ethernet source address.")

    parser.add_option("-s", "--ip_source",
                      dest="ip_source", default=None,
                      help="The IP source address.")

    parser.add_option("-G", "--igmp_group",
                      dest="igmp_group", default=None,
                      help="The IPv4 group to spoof a leave message for.")

    parser.add_option("-A", "--no-router-alert",
                      action="store_true", dest="no_ra",
                      help="Disable the use of the IP Router Alert option.")

    (options, args) = parser.parse_args()

    if options.igmp_group is None or \
       options.ether_source is None or \
       options.ether_iface is None or \
       options.ip_source is None:
           print "A required argument is missing."
           return

    # Set up the vanilla packet
    ether = ethernet()
    ether.type = 0x0800
    ether.src = ether_atob(options.ether_source)
    ether.dst = "\x01\x00\x5e\x00\x00\x02"

    ip = ipv4()
    ip.version = 4
    ip.hlen = 5
    ip.tos = 0
    ip.id = 123
    ip.flags = 0x02		# DF bit
    ip.offset = 0
    ip.ttl = 1
    ip.protocol = IPPROTO_IGMP
    ip.src = inet_atol(options.ip_source)
    ip.dst = inet_atol("224.0.0.2")		# XXX should be a constant

    igmp = igmpv2()
    igmp.type = IGMP_HOST_LEAVE_MESSAGE
    igmp.code = 0
    igmp.group = inet_atol(options.igmp_group)

    igmp_packet = Chain([igmp])
    igmp.checksum = igmp_packet.calc_checksum()

    if options.no_ra is True:
	ip.length = len(ip.bytes) + len(igmp.bytes)
	ip.hlen = len(ip.bytes) >> 2
    else:
	ra = pcs.TypeLengthValueField("ra",
				      pcs.Field("", 8, default = 148),
				      pcs.Field("", 8),
				      pcs.Field("", 16))
	ip.options.append(ra)
	ip.hlen = len(ip.bytes) >> 2
	ip.length = len(ip.bytes) + len(igmp.bytes)

    ip.checksum = ip.cksum()
    packet = Chain([ether, ip, igmp])

    output = PcapConnector(options.ether_iface)

    packet.encode()
    out = output.write(packet.bytes, len(packet.bytes))

main()
