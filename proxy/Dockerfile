FROM ubuntu:20.04

RUN apt-get -y update
RUN apt-get -y upgrade

# For route
RUN apt-get install -y net-tools 


RUN apt-get install -y gcc make git
RUN git clone https://github.com/z3apa3a/3proxy
RUN cd 3proxy && ln -s Makefile.Linux Makefile && make && make install

RUN apt-get install -y tcpdump
RUN apt install -y dante-server
RUN apt install -y curl

COPY danted.conf /etc/danted.conf
COPY 3proxy.cfg /usr/local/3proxy/conf/3proxy.cfg

# CMD danted & service 3proxy start & tcpdump -i eth1 -n -w /pcap/proxy-$(date +%Y-%m-%d-%H-%M-%S).pcap
CMD service 3proxy start; tcpdump -U -w /pcap/proxy-$(date +%Y-%m-%d-%H-%M-%S).pcap
