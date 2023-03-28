FROM selenium/standalone-chrome:4.8.0

RUN sudo apt-get -y update

# For route
RUN sudo apt-get install -y net-tools 

WORKDIR /app

COPY configure.sh .

# for testing
RUN sudo apt-get install -y tcpdump 
