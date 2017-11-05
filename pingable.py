#!/usr/bin/python

import os
import sys
import struct
import socket
import time

DEV = "/dev/net/test"
ACCEPT_ANY_IP = False

MY_MAC = "".join(map(chr, [0x00, 0x11, 0x22, 0x33, 0x44, 0x55]))
MY_IP = "".join(map(chr, [0x0a, 0x0a, 0x0a, 0x0a]))

ETH_P_IP = 0x0800
ETH_P_ARP = 0x0806

IPPROTO_ICMP = 1
IPPROTO_TCP = 6
IPPROTO_UDP = 17

ICMP_ECHOREPLY = 0
ICMP_ECHO = 8


def process_arp(dst, src, data):
    arp = struct.unpack("!HHBBH6s4s6s4s", data[:28])

    if arp[4] != 1:
        return

    print("RX: ARP req for {} from {}".format(socket.inet_ntoa(arp[8]), socket.inet_ntoa(arp[6])))

    if arp[8] != MY_IP and not ACCEPT_ANY_IP:
        return

    reply = struct.pack("!HHBBH6s4s6s4s",
        arp[0], arp[1], arp[2], arp[3], 2,
        MY_MAC, MY_IP, arp[5], arp[6])

    print("==>\tIt's me!")

    return reply


def checksum(msg):

    def carry_around_add(a, b):
        c = a + b
        return (c & 0xffff) + (c >> 16)

    s = 0
    for i in range(0, len(msg), 2):
        w = ord(msg[i]) + (ord(msg[i+1]) << 8)
        s = carry_around_add(s, w)
    return ~s & 0xffff


def process_ip_icmp(src_ip, data):
    icmp_header = struct.unpack("!BBHHH", data[:8])
    payload = data[8:]

    if (icmp_header[0] != ICMP_ECHO and icmp_header[1] != 0):
        return

    print ("RX: ICMP ping from {}".format(src_ip))

    reply = struct.pack("!BBHHH",
        ICMP_ECHOREPLY, 0,
        0, # checksum
        icmp_header[3], icmp_header[4]) + payload

    cs = checksum(reply)
    reply = reply[:2]  + chr(cs & 0xff) + chr(cs >> 8)+ reply[4:]

    return reply


def process_ip(data):
    reply = None

    ip_header = struct.unpack("!BBHHHBBH4s4s", data[:20])
    # FIXME: IP header is variable length and can have options
    payload = data[20:]

    dst = socket.inet_ntoa(ip_header[9])
    src = socket.inet_ntoa(ip_header[8])
    proto = ip_header[6]

    if proto == IPPROTO_ICMP:
        reply = process_ip_icmp(src, payload)
    elif proto == IPPROTO_UDP:
        print("RX: IP/UDP dst {}, src {}, len: {}".format(dst, src, len(payload)))
    elif proto == IPPROTO_TCP:
        print("RX: IP/TCP dst {}, src {}, len: {}".format(dst, src, len(payload)))
    else:
        print("RX: IP dst {}, src {}, len: {}".format(dst, src, len(payload)))

    if reply is not None:
        i = ip_header
        reply = struct.pack("!BBHHHBBH4s4s",
            i[0], i[1], i[2], i[3], i[4],
            75, i[6],
            0, # header checksum
            i[9], i[8]) + reply

        cs = checksum(reply[0:20])
        reply = reply[:10]  + chr(cs & 0xff) + chr(cs >> 8)+ reply[12:]

    return reply


def process_packet(data):
    reply = None

    (dst, src, ethertype) = struct.unpack("!6s6sH", data[:14])
    payload = data[14:]

    if ethertype == ETH_P_ARP:
        reply = process_arp(dst, src, payload)
    elif ethertype == ETH_P_IP:
        reply = process_ip(payload)
    else:
        print("RX: unknown dst {}, src {}, ethertype {}, len: {}".format(
            map(ord, dst), map(ord, src), ethertype, len(payload)))

    if reply is not None:
        return struct.pack("!6s6sH", src, MY_MAC, ethertype) + reply


def pad_packet(data):
    if len(data) >= 64:
        return data

    return data + ("\0"*(64-len(data)))


def main():

    fd = os.open(DEV, os.O_RDWR)
    try:
        while True:
#            time.sleep(0.5)

            try:
                data = os.read(fd, 2048)
            except Exception, e:
                print("can't read: {}".format(e))
                continue

            try:
                res = process_packet(data)
            except Exception, e:
                print("can't handle packet: {}".format(e))
                continue

            if res:
                res = pad_packet(res)
                try:
                    os.write(fd, res)
                except Exception, e:
                    print("can't write: {}".format(e))
                    continue

    finally:
        os.close(fd)


if __name__ == '__main__':
    main()
