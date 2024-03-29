#!/bin/bash

# iptables --table nat --append POSTROUTING --out-interface eth0 -j MASQUERADE
# iptables --append FORWARD --in-interface eth1 -j ACCEPT

########################################################################
# Define various configuration parameters.
########################################################################

SOCKS_PORT=8899
SOCKS_HOST=$(getent ahosts $SOCKS_HOST | awk '{ print $1 ; exit }')
REDSOCKS_TCP_PORT=$(expr $SOCKS_PORT + 1)
REDSOCKS_UDP_PORT=$(expr $SOCKS_PORT + 2)
TMP=/tmp/subnetproxy ; mkdir -p $TMP
REDSOCKS_LOG=/log/redsocks.log
REDSOCKS_CONF=$TMP/redsocks.conf
SUBNET_INTERFACE=eth1
SUBNET_ADDRESS=$(ip -f inet addr show $SUBNET_INTERFACE | sed -En -e 's/.*inet ([0-9.]+).*/\1/p')
# SUBNET_PORT_ADDRESS="192.168.2.1" #can't be the same subnet as eth1
INTERNET_INTERFACE=eth0
# SUDO_COMMAND="sudo"
SUDO_COMMAND=""


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

# iptables --table nat --append POSTROUTING --out-interface eth0 -j MASQUERADE
# iptables --append FORWARD --in-interface eth1 -j ACCEPT

########################################################################
#redsocks configuration
########################################################################

cat >$REDSOCKS_CONF <<EOF
base {
  log_info = on;
  // log_debug = on;
  log = "file:$REDSOCKS_LOG";
  daemon = on;
  redirector = iptables;
}
redsocks {
  bind = "0.0.0.0:$REDSOCKS_TCP_PORT";
  relay = "$SOCKS_HOST:$SOCKS_PORT";
  type = socks5;
}
redudp {
	bind = "$SUBNET_ADDRESS:$REDSOCKS_UDP_PORT";
	relay = "$SOCKS_HOST:$SOCKS_PORT";
	type = socks5;
	udp_timeout = 30;
	udp_timeout_stream = 180;
}
EOF

# To use tor just change the redsocks output port from 1080 to 9050 and
# replace the ssh tunnel with a tor instance.

########################################################################
# start redsocks
########################################################################

$SUDO_COMMAND redsocks2 -c $REDSOCKS_CONF -p /dev/null

########################################################################
# proxy iptables setup
########################################################################

# create the REDSOCKS target
$SUDO_COMMAND iptables -t nat -N REDSOCKS

# don't route unroutable addresses
$SUDO_COMMAND iptables -t nat -A REDSOCKS -d 0.0.0.0/8 -j RETURN
$SUDO_COMMAND iptables -t nat -A REDSOCKS -d 10.0.0.0/8 -j RETURN
$SUDO_COMMAND iptables -t nat -A REDSOCKS -d 127.0.0.0/8 -j RETURN
$SUDO_COMMAND iptables -t nat -A REDSOCKS -d 169.254.0.0/16 -j RETURN
$SUDO_COMMAND iptables -t nat -A REDSOCKS -d 172.16.0.0/12 -j RETURN
$SUDO_COMMAND iptables -t nat -A REDSOCKS -d 192.168.0.0/16 -j RETURN
$SUDO_COMMAND iptables -t nat -A REDSOCKS -d 224.0.0.0/4 -j RETURN
$SUDO_COMMAND iptables -t nat -A REDSOCKS -d 240.0.0.0/4 -j RETURN

# redirect statement sends everything else to the redsocks
# proxy input port
$SUDO_COMMAND iptables -t nat -A REDSOCKS -p tcp -j REDIRECT --to-ports $REDSOCKS_TCP_PORT

# if it came in on eth0, and it is tcp, send it to REDSOCKS
$SUDO_COMMAND iptables -t nat -A PREROUTING -i $SUBNET_INTERFACE -p tcp -j REDSOCKS

# Use this one instead of the above if you want to proxy the local
# networking in addition to the subnet stuff. Redsocks listens on
# all interfaces with local_ip = 0.0.0.0 so no other changes are
# necessary.
#$SUDO_COMMAND iptables -t nat -A PREROUTING -p tcp -j REDSOCKS

# don't forget to accept the tcp packets from eth0
$SUDO_COMMAND iptables -A INPUT -i $SUBNET_INTERFACE -p tcp --dport $REDSOCKS_TCP_PORT -j ACCEPT


# UDP routing
ip rule add fwmark 0x01/0x01 table 100
ip route add local 0.0.0.0/0 dev lo table 100
iptables -t mangle -N REDSOCKS2

# iptables -t mangle -A REDSOCKS2 -d 0.0.0.0/8 -j RETURN
# iptables -t mangle -A REDSOCKS2 -d 10.0.0.0/8 -j RETURN
# iptables -t mangle -A REDSOCKS2 -d 127.0.0.0/8 -j RETURN
# iptables -t mangle -A REDSOCKS2 -d 169.254.0.0/16 -j RETURN
# iptables -t mangle -A REDSOCKS2 -d 172.16.0.0/12 -j RETURN
# iptables -t mangle -A REDSOCKS2 -d 192.168.0.0/16 -j RETURN
# iptables -t mangle -A REDSOCKS2 -d 224.0.0.0/4 -j RETURN
# iptables -t mangle -A REDSOCKS2 -d 240.0.0.0/4 -j RETURN

iptables -t mangle -A REDSOCKS2 -p udp -j TPROXY --on-port $REDSOCKS_UDP_PORT --tproxy-mark 0x01/0x01
iptables -t mangle -A PREROUTING -i $SUBNET_INTERFACE -p udp -j REDSOCKS2

# Proxy UDP without going through socks5 proxy
# iptables --table nat --append POSTROUTING --out-interface $INTERNET_INTERFACE -p udp -j MASQUERADE
# iptables --append FORWARD --in-interface $SUBNET_INTERFACE -p udp -j ACCEPT
# iptables -A FORWARD -i $INTERNET_INTERFACE -o $SUBNET_INTERFACE -m state --state ESTABLISHED,RELATED -p udp -j ACCEPT
