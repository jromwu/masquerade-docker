FROM rust:1.68

RUN apt-get -y update
RUN apt-get -y upgrade

RUN apt install -y cmake
RUN apt install -y git

RUN git clone https://github.com/jromwu/masquerade.git
# COPY ./masquerade /masquerade
WORKDIR /masquerade
RUN cargo build

# For route
RUN apt-get install -y net-tools tcpdump

COPY configure.sh /

CMD /configure.sh; echo hello world; RUST_LOG="debug" cargo run --bin client -- "$SERVER_ADDR" "$LISTEN_ADDR" socks5 > /log/client-$(date +%Y-%m-%d-%H-%M-%S).log 2>&1; tail -f /dev/null