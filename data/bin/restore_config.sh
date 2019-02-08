#!bin/sh

PING_INTERVAL=10
while [ 1 ] ; do
      STATUS=`curl -w '%{http_code}\n' -s -o /dev/null http://localhost:8080/json/ping`
      if [ x"$STATUS" = x200 ] ; then
        break
      else
        sleep $PING_INTERVAL
      fi
done

rm -rf /tmp/config
mkdir -p /tmp/config
cp -f /var/lib/elasticsearch/backup/* /tmp/config/

elasticdump --output=http://localhost:9200/.fess_config.data_config --input=/tmp/config/datastore.json
elasticdump --output=http://localhost:9200/.fess_config.label_type --input=/tmp/config/label.json
elasticdump --output=http://localhost:9200/.fess_config.data_config_to_label --input=/tmp/config/data_config_to_label.json
elasticdump --output=http://localhost:9200/.fess_config.scheduled_job --input=/tmp/config/scheduled_job.json
#elasticdump --output=http://localhost:9200/.fess_config.crawling_info --input=/tmp/config/crawl.json
elasticdump --output=http://localhost:9200/.fess_config.key_match --input=/tmp/config/key_match.json

rm -rf /tmp/config

