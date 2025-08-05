#!/bin/bash
# set -eux
pkill -9 main
pkill -9 firecracker

# ./test.py ./test-2inputs.json

setsid ./main --host=0.0.0.0 --port=8080 &> /users/id_17/faasnap/faasnap/faasnap.log &
./prepare-faasnap.py faasnap ./test-2inputs.json 