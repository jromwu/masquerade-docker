#!/bin/bash

sudo route del default
sudo route add default gateway gateway

sudo chown seluser:seluser /user-data