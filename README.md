# GL-kernel-net

## Task description

Device driver must provide a /dev/ character node for userspace applications.

On Open, driver creates designated network interface testN. Close removes the
network interface.

Every packet Linux sends to the interface is placed into a buffer and it can
be read by the process this interface belongs to, and the opposite
way - written packets should be received and processed by the OS.

One packet - one syscall. (Read and write operate on complete packets).
Userspace process should block on read if no data available.

## Bonus points for:

* Interface (ifconfig) and ethtool (ethtool -S) statistics.

* Multiple RX and TX buffers to avoid packet loss.

* Non-blocking IO support.

## Hints
To send and receive traffic, interface must be UP and have IP address
assigned. For example:
```
# ip link set up dev test0
# ip addr add 10.10.10.1/24 dev test0
```

Watch out for NetworkManager, it may take over the device management.

Look how other drivers work. For example: loopback, dummy, veth, tun.

## Testing the driver
Optionally, you may use the `pingable.py` Python 2 script, which opens
device node, handles basic traffic flow and handles ARP and ICMP Ping
packets. Script can be modified to suit the needs better if necessary.

### Usage example

After the script start, new interface is created, IPv6 stuff start to
happen and NetworkManager tries to configure IPv4:
```
# python pingable.py

RX: unknown dst [51, 51, 0, 0, 0, 22], src [6, 5, 208, 93, 13, 96], ethertype 34525, len: 76
RX: IP/UDP dst 255.255.255.255, src 0.0.0.0, len: 308
RX: unknown dst [51, 51, 255, 171, 84, 154], src [6, 5, 208, 93, 13, 96], ethertype 34525, len: 64
RX: unknown dst [51, 51, 0, 0, 0, 22], src [6, 5, 208, 93, 13, 96], ethertype 34525, len: 76
RX: unknown dst [51, 51, 0, 0, 0, 22], src [6, 5, 208, 93, 13, 96], ethertype 34525, len: 76
RX: unknown dst [51, 51, 0, 0, 0, 2], src [6, 5, 208, 93, 13, 96], ethertype 34525, len: 48
RX: unknown dst [51, 51, 0, 0, 0, 22], src [6, 5, 208, 93, 13, 96], ethertype 34525, len: 76
RX: unknown dst [51, 51, 0, 0, 0, 2], src [6, 5, 208, 93, 13, 96], ethertype 34525, len: 48
RX: IP/UDP dst 255.255.255.255, src 0.0.0.0, len: 308
...
```

In another terminal window new interface can be configured:
```
# ip a s dev test0
8: test0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UNKNOWN qlen 1000
    link/ether ea:83:83:db:e0:4f brd ff:ff:ff:ff:ff:ff
    inet6 fe80::1eb0:8ef4:e7ec:1d3/64 scope link
       valid_lft forever preferred_lft forever
# ip a a 10.10.10.1/24 dev test0
```

Ping should work now:
```
# ip a a 10.10.10.1/24 dev test0
# ping 10.10.10.10
PING 10.10.10.10 (10.10.10.10) 56(84) bytes of data.
64 bytes from 10.10.10.10: icmp_seq=1 ttl=75 time=5.22 ms
64 bytes from 10.10.10.10: icmp_seq=2 ttl=75 time=65.8 ms
64 bytes from 10.10.10.10: icmp_seq=3 ttl=75 time=1.91 ms
...
```

And `pingable.py` window:
```
...
RX: ARP req for 10.10.10.10 from 10.10.10.1
==>	It's me!
RX: ICMP ping from 10.10.10.1
RX: ICMP ping from 10.10.10.1
RX: ICMP ping from 10.10.10.1
...
```
