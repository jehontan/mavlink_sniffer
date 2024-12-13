import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("",9690))

while True:
    print('RX...')
    data, addr = sock.recvfrom(2048)
    print(data[0])
    if data[0] == 0xFE:
        print('Mavlink msg!')
        print('Msg Len:', data[1])
        print('Msg ID:', data[5])