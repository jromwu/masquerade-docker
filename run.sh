#!/bin/bash

for (( i=0; i<$1; i++ )); { export TARGET="$TARGET" CHROME_SETUP="$CHROME_SETUP"; sudo docker compose build && sudo docker compose up --force-recreate --remove-orphans --abort-on-container-exit --exit-code-from=client; }
