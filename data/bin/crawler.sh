#!/bin/bash

PING_INTERVAL=600
chmod -R 777 /var/lib/elasticsearch/csv
while [ 1 ] ; do
      STATUS=`curl -w '%{http_code}\n' -s -o /dev/null http://localhost:8080/json/ping`
      if [ x"$STATUS" = x200 ] ; then
        python /var/lib/elasticsearch/bin/crawl_radar.py /var/lib/elasticsearch/bin/radar.yaml radar_en
        mv /tmp/radar_experiment_en.csv /var/lib/elasticsearch/csv/experiments/
        chmod -R 777  /var/lib/elasticsearch/csv
      else
        service fess restart
      fi
        sleep $PING_INTERVAL
done


