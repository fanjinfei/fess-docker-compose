import hashlib

import sys
import multiprocessing
import re
import requests
import logging
import yaml
import json

import csv
import unicodecsv
import codecs
import traceback

import time
from datetime import datetime

#export PYTHONWARNINGS="ignore:Unverified HTTPS request"
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


from crawler_base3 import write_csv, read_csv
class Crawler():
    def __init__(self, data):
        self.conf = data
    def get_sourceRepo(self, url, sid):
        data = {"operationName":None,
                "query":"{sourceRepositoryById(id:\""+str(sid)+"\"){id webUrl readme charter __typename}}"
                }
        ''' query { sourceRepositories(orderBy: ID_ASC) {
  nodes{ id readme webUrl }         } } 
    query { hackathons(orderBy: ID_ASC) {
  nodes{ id  name description sourceRepositoryId}         } }'''
        print data
        r = requests.post(url=url, data=data, timeout=10)
        if r.status_code != requests.codes.ok:
            print r
            return None
        source = json.loads(r.text)
        #import pdb; pdb.set_trace()
        #print source['data']['sourceRepositoryById']['webUrl']    
        return source['data']['sourceRepositoryById']['charter']
    def process(self):
        print self.conf
        url = self.conf['start_links'][0]
        #self.get_sourceRepo(url, "7")
        #sys.exit(0)
        
        data = {  
#   "operationName":None,
   "variables":{  

   },
   "query":'''{ experiments(orderBy: CREATED_AT_DESC) {
                nodes {
                  ...ExperimentData
                  __typename
                }
                __typename
              }
            }

            fragment ExperimentData on Experiment {
              id
              name
              description
              conclusion
              concludedAt
              createdBy
              createdAt
              updatedAt
              sourceRepositoryId
              __typename
            }
        '''
}
        #data = json.loads(data)
        print data
        r = requests.post(url=url, data=data, timeout=10)
        res = None
        if r.status_code == requests.codes.ok:
            print r.text[-200:]
            res = json.loads(r.text)
        if not res: return
        for e in res['data']['experiments']['nodes']:
            sid = e['sourceRepositoryId']
            print '--'.join([e['id'], e['name'], e['description'], str(sid)])
            if not sid: continue
            charter = self.get_sourceRepo(url, str(sid))
            charter = charter.replace('\n', ' ') if charter else ''
            charter = charter.replace('\t', ' ')
            charter = charter.replace('\r', ' ')
            print charter


def read_config(filename):
    with open(filename) as f:
    # use safe_load instead load
        return yaml.safe_load(f)

def main():
    logging.basicConfig(format='%(asctime)s %(message)s',
                         filename='/tmp/radar_crawler.log', level=logging.INFO) #INFO, DEBUG
    confs = read_config(sys.argv[1])
    for conf in confs:
        for short_name, data in conf.iteritems():
            print '"'+short_name+'"'
            if not data.get('enabled', True):
                continue
            craw = Crawler(data)
            craw.process()
    return
    
if sys.argv[1] =='test':
    test()
else:
    main()
