#!/bin/bash

for (( i=0; i<$2; i++ )); { sudo docker compose build && sudo TARGET="$1" CHROME_SETUP="$CHROME_SETUP" docker compose up --force-recreate --remove-orphans --abort-on-container-exit --exit-code-from=client; }
