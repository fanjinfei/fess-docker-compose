#!/bin/sh

rm -rf /tmp/config
mkdir -p /tmp/config
elasticdump --input=http://localhost:9200/.fess_config.data_config --output=/tmp/config/datastore.json
elasticdump --input=http://localhost:9200/.fess_config.label_type --output=/tmp/config/label.json
elasticdump --input=http://localhost:9200/.fess_config.data_config_to_label --output=/tmp/config/data_config_to_label.json
elasticdump --input=http://localhost:9200/.fess_config.scheduled_job --output=/tmp/config/scheduled_job.json
elasticdump --input=http://localhost:9200/.fess_config.crawling_info --output=/tmp/config/crawl.json
elasticdump --input=http://localhost:9200/.fess_config.key_match --output=/tmp/config/key_match.json

cp -f /tmp/config/* /var/lib/elasticsearch/backup
rm -rf /tm/config
