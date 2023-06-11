#!/bin/bash

tc qdisc add dev eth1 root netem delay 80ms 20ms

route del default
route add default gw capturer eth1
