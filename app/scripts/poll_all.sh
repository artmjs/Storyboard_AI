#!/usr/bin/env bash
# poll every 2 seconds and pretty-print the json list of all jobs
while true; do
  curl -s http://127.0.0.1:8001/api/sketch/status | jq
  sleep 2
done