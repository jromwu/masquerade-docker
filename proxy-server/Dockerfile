FROM rust:1.68

RUN apt-get -y update
RUN apt-get -y upgrade

RUN apt install -y cmake
RUN apt install -y git

# RUN git clone https://github.com/jromwu/masquerade.git
WORKDIR /masquerade
# RUN cargo build

RUN apt install -y tcpdump

CMD tcpdump -n -U -w /pcap/proxy-$(date +%Y-%m-%d-%H-%M-%S).pcap & RUST_LOG="debug" cargo run --bin server -- "$LISTEN_ADDR" > /log/server-$(date +%Y-%m-%d-%H-%M-%S).log 2>&1; tail -f /dev/null
# CMD tail -f /dev/null
