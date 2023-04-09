#!/bin/bash

for (( i=0; i<$1; i++ )); { sudo docker compose build && sudo docker compose up --force-recreate --remove-orphans --abort-on-container-exit --exit-code-from=client; }
