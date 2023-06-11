#!/bin/bash

# iptables --table nat --append POSTROUTING --out-interface eth0 -j MASQUERADE
# iptables --append FORWARD --in-interface eth1 -j ACCEPT

########################################################################
# Define various configuration parameters.
########################################################################

SUBNET_INTERFACE=eth1
SUBNET_ADDRESS=$(ip -f inet addr show $SUBNET_INTERFACE | sed -En -e 's/.*inet ([0-9.]+).*/\1/p')
# SUBNET_PORT_ADDRESS="192.168.2.1" #can't be the same subnet as eth1
INTERNET_INTERFACE=eth0


########################################################################
#standard router setup - sets up subnet SUBNET_PORT_ADDRESS/24 on eth0
########################################################################

# note - if you just want a standard router without the proxy/tunnel
# business, you only need to execute this block of code.

# $SUDO_COMMAND sh -c "echo 1 > /proc/sys/net/ipv4/ip_forward"
# $SUDO_COMMAND ifconfig $SUBNET_INTERFACE $SUBNET_PORT_ADDRESS netmask 255.255.255.0
# $SUDO_COMMAND iptables -A FORWARD -o $INTERNET_INTERFACE -i $SUBNET_INTERFACE -s $SUBNET_PORT_ADDRESS/24 \
#      -m conntrack --ctstate NEW -j ACCEPT
# $SUDO_COMMAND iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED \
#      -j ACCEPT
# $SUDO_COMMAND iptables -A POSTROUTING -t nat -j MASQUERADE

iptables --table nat --append POSTROUTING --out-interface $INTERNET_INTERFACE -j MASQUERADE
iptables --append FORWARD --in-interface $SUBNET_INTERFACE -j ACCEPT
iptables -A FORWARD -i $INTERNET_INTERFACE -o $SUBNET_INTERFACE -m state --state ESTABLISHED,RELATED -j ACCEPT

# Add latency, jitter, etc. for traffic back
tc qdisc add dev $SUBNET_INTERFACE root netem delay 80ms 20ms
