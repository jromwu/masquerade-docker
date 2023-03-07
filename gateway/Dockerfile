FROM ubuntu:20.04

RUN apt-get -y update
RUN apt-get -y upgrade

RUN apt-get install -y iptables
RUN apt-get install -y net-tools netcat
RUN apt-get install -y libevent-dev libssl-dev

WORKDIR /app

COPY configure.sh .

COPY --chmod=777 redsocks2 /usr/local/bin/redsocks
