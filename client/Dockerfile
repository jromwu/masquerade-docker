FROM ubuntu:20.04

RUN apt-get -y update
RUN apt-get -y upgrade

# For route
RUN apt-get install -y net-tools 

COPY configure.sh .
