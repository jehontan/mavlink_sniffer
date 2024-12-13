import socket
from mavlink_messages import *

ETH_P_ALL = 3
ETH_P_IP = 0x800
PROTO_UDP = 17
sock = socket.socket(socket.AF_PACKET, socket.SOCK_DGRAM, socket.htons(ETH_P_IP))
sock.bind(("lo", 0))

def parse_mav(data):
    if data[0] != 0xfe:
        return
    
    msg = MavlinkMessage.unpack(data[1:])
    print(msg.payload)

while True:
    data = sock.recv(2048)
    ihl = (data[0] & 0b1111) * 4 # number of bytes in header
    version = data[0] >> 4

    if version == 4:
        protocol = data[9]
        mav_packet = data[28:]
        parse_mav(mav_packet)
    elif version == 6:
        # Untested
        protocol = data[6]
        mav_packet = data[40:]
        parse_mav(mav_packet)
    else:
        print("Malformed IP packet")