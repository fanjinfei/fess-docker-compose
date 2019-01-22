#!/bin/sh

elasticdump --input=http://localhost:9200/.fess_config.label_type --output=/var/lib/elasticsearch/backup/label.json
elasticdump --input=http://localhost:9200/.fess_config.crawling_info --output=/var/lib/elasticsearch/backup/crawl.json
elasticdump --input=http://localhost:9200/.fess_config.data_config --output=/var/lib/elasticsearch/backup/datastore.json
elasticdump --input=http://localhost:9200/.fess_config.key_match --output=/var/lib/elasticsearch/backup/key_match.json
