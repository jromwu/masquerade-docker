#!/bin/bash

for (( i=0; i<$1; i++ )); { docker compose build && docker compose up --force-recreate --remove-orphans --abort-on-container-exit --exit-code-from=client; }
