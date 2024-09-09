#!/bin/bash

docker run --rm --name=prometheus --network host -p 9090:9090 -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus