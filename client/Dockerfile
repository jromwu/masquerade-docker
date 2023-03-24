FROM python:3
# FROM ubuntu:20.04

RUN apt-get -y update

# For route
RUN apt-get install -y net-tools 

RUN apt install -y curl

WORKDIR /usr/src/app

COPY configure.sh .

# For cv2 python library for video capturing
RUN apt-get install -y ffmpeg

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/* .

CMD ./configure.sh && python3 ./test_selenium_form.py
