FROM ubuntu:20.04

RUN apt-get -y update
RUN apt-get -y upgrade

RUN apt-get install -y iptables iproute2
RUN apt-get install -y net-tools netcat

WORKDIR /app

RUN apt-get install -y tcpdump

COPY configure.sh .
RUN chmod +x configure.sh
CMD ./configure.sh
