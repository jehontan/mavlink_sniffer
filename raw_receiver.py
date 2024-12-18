import pcap
import dpkt
from mavlink_messages import *

cap = pcap.pcap('lo', immediate=True)

def parse_mav(data):
    if data[0] != 0xfe:
        return
    
    msg = MavlinkMessage.unpack(data[1:])
    print(msg.payload)

def handle_packet(timestamp, packet, *args):
    # data = sock.recv(2048)
    eth = dpkt.ethernet.Ethernet(packet)

    if not isinstance(eth.data, dpkt.ip.IP):
        return

    data : dpkt.udp.UDP = eth.data.data.data
    print(timestamp)
    parse_mav(data)


while True:
    packets = cap.readpkts()
    for timestamp, pkt in packets:
        handle_packet(timestamp, pkt)