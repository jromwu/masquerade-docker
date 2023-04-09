#!/bin/bash

for (( i=0; i<$1; i++ )); { sudo docker compose build && sudo TARGET="$TARGET" CHROME_SETUP="$CHROME_SETUP" docker compose up --force-recreate --remove-orphans --abort-on-container-exit --exit-code-from=client; }
