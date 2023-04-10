#!/bin/bash
output="run_progress"
remove_to_terminate="remove_to_terminate"

echo "Target: $1. Num of runs: $2."
echo "Remove ${remove_to_terminate} to terminate after the current run finishes."

echo "Target: $1. Num of runs: $2" > "$output"
echo "remove this file to terminate run" > "$remove_to_terminate"
for (( i=0; i<$2; i++ )); do 
    if [[ -f "$remove_to_terminate" ]]; then
        echo "Run $(($i + 1)) of $2"
        echo "Run $(($i + 1)) of $2" >> "$output"
        sudo docker compose build && sudo TARGET="$1" CHROME_SETUP="$CHROME_SETUP" docker compose up --force-recreate --remove-orphans --abort-on-container-exit --exit-code-from=client
        exit_code=$?
        if [ $exit_code -ne 0 ]; then
            echo "docker exited with code ${exit_code}" >> "$output"
        fi
    else
        echo "Detected ${remove_to_terminate} deleted. Terminating."
        echo "Finished $(($i + 1)) runs out of $2."
        echo "Detected ${remove_to_terminate} deleted. Terminating." >> "$output"
        exit 1
    fi
done

rm $remove_to_terminate
exit 0
