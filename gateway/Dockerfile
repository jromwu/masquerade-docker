FROM ubuntu:20.04

RUN apt-get -y update
RUN apt-get -y upgrade

RUN apt-get install -y iptables iproute2
RUN apt-get install -y net-tools netcat

WORKDIR /app

RUN apt-get install -y git gcc make libevent-dev libssl-dev \
    && git clone https://github.com/semigodking/redsocks.git \
    && cd redsocks && make DISABLE_SHADOWSOCKS=true \
    && cp redsocks2 /usr/bin/redsocks2 \
    && cd .. && rm -rf redsocks \
    && apt-get remove -y git gcc make libevent-dev libssl-dev

RUN apt-get install -y tcpdump

COPY configure.sh .
RUN chmod +x configure.sh
CMD ./configure.sh
