import time
from pymavlink import mavutil

conn = mavutil.mavlink_connection('udpbcast:127.0.0.1:9690')

i = 0
while True:
    msg = conn.mav.heartbeat_send(0, 1, 0, 0, 4)
    print('Sent', i)
    i  = (i+1) % 256
    time.sleep(0.01)