#!/bin/bash

docker run --rm --network host -p 3000:3000 --name=grafana grafana/grafana:latest