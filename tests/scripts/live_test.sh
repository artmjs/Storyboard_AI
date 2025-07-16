#!/usr/bin/env bash
set -euo pipefail

API=http://127.0.0.1:8001
SKETCH_PATH="test_images/test_sketch_3.png"

echo "1) Submitting initial refine..."
RESP=$(curl -s -X POST "$API/api/sketch/refine" \
  -F "file=@${SKETCH_PATH}")
echo "-> $RESP"

IMAGE_ID=$(jq -r .image_id <<<"$RESP")
JOB1=$(jq -r .job_id   <<<"$RESP")
echo "   image_id=$IMAGE_ID, job_id=$JOB1"

echo
echo "2) Polling status for job $JOB1"
while true; do
  S=$(curl -s "$API/api/sketch/status/$JOB1" | jq -r .status)
  echo "   status: $S"
  [[ "$S" == "SUCCESS" || "$S" == "FAILURE" ]] && break
  sleep 5
done

URL1=$(jq -r .url <<<"$(curl -s "$API/api/sketch/status/$JOB1")")
echo "3) Downloading refined image -> out_v1.png"
curl -s "$API${URL1}" -o out_v1.png

echo
echo "4) Submitting multi-turn edit..."
EDIT_PROMPT="Add another person to the left side of the frame that looks to the right."
EDIT_RESP=$(curl -s -X POST "$API/api/sketch/edit" \
  -H "Content-Type: application/json" \
  -d '{"image_id":"'"$IMAGE_ID"'","prompt":"'"$EDIT_PROMPT"'"}')
echo "-> $EDIT_RESP"

JOB2=$(jq -r .job_id <<<"$EDIT_RESP")
echo "   edit job_id=$JOB2"

echo
echo "5) Polling status for job $JOB2"
while true; do
  S2=$(curl -s "$API/api/sketch/status/$JOB2" | jq -r .status)
  echo "   status: $S2"
  [[ "$S2" == "SUCCESS" || "$S2" == "FAILURE" ]] && break
  sleep 5
done

URL2=$(jq -r .url <<<"$(curl -s "$API/api/sketch/status/$JOB2")")
echo "6) Downloading edited image -> out_v2.png"
curl -s "$API${URL2}" -o out_v2.png

echo
echo " Done! Check out:"
echo "   out_v1.png"
echo "   out_v2.png"
