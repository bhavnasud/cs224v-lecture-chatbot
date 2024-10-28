#!/bin/bash
# Recommended way to run Grobid is to have docker installed. See details here: https://grobid.readthedocs.io/en/latest/Grobid-docker/

if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker before running Grobid."
    exit 1
fi


machine_arch=$(uname -m)

docker run -t --rm -p 8070:8070 --platform linux/amd64 lfoppiano/grobid:0.7.1
