FROM selenium/standalone-chrome:4.8.0

RUN sudo apt-get -y update
RUN sudo apt-get -y upgrade

# For route
RUN sudo apt-get install -y net-tools 

WORKDIR /app

COPY configure.sh .

# for testing
RUN sudo apt-get install -y tcpdump netcat
