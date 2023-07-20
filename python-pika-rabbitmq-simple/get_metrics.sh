#!/bin/bash

echo "****"
echo "**** http://127.0.0.1:15692/metrics/ "
echo "****"
curl -i http://127.0.0.1:15692/metrics/ 

echo "****"
echo "**** http://127.0.0.1:15672/api/queues "
echo "****"
curl -i -u guest:guest -H "content-type:application/json" http://127.0.0.1:15672/api/queues