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
        try:
            r = requests.post(url=url, data=data, timeout=10)
        except:
            s = traceback.format_exc()
            print url, sid, data, s
            return None
        if r.status_code != requests.codes.ok:
            print r
            return None
        source = json.loads(r.text)
        #import pdb; pdb.set_trace()
        #print source['data']['sourceRepositoryById']['webUrl']    
        return source['data']['sourceRepositoryById']['charter']
    def get_tags(self, url):
        data = {"operationName":None,
                "query": "{ tags( orderBy:ID_ASC) {nodes {id name}}}"
                }
        try:
            r = requests.post(url=url, data=data, timeout=10)
        except:
            s = traceback.format_exc()
            print url, s
            return None
        if r.status_code != requests.codes.ok:
            print r
            return None
        source = json.loads(r.text)
        res = {}
        for node in source['data']['tags']['nodes']:
            res[node['id']] = node['name']
        print res
        return res
    def get_etags(self, tags, etags):
        res = []
        for tag in etags:
            tag_name = tags.get(tag['tagId'], None)
            if tag_name:
                res.append(tag_name)
        return res
    def get_hackathons(self, tags):
        url = self.conf['start_links'][0]
        last_crawled = datetime.utcnow().isoformat()[:23]+'Z' #str(int(time.time()))
        data = { "query": "{ hackathons(orderBy: ID_ASC) { \
  nodes{ id  name description hackathonTags { nodes {tagId} } updatedAt sourceRepositoryId}         } }"
        }
        r = requests.post(url=url, data=data, timeout=10)
        res = None
        if r.status_code == requests.codes.ok:
            print r.text[-200:]
            res = json.loads(r.text)
        if not res: return
        hs = []
        for e in res['data']['hackathons']['nodes']:
            sid = e['sourceRepositoryId']
            last_modified = e['updatedAt'][:23]+'Z'
            htags = e['hackathonTags']['nodes']
            htags = self.get_etags(tags, htags)
            if not htags:
                htags = '[""]'
            else:
                htags = json.dumps(htags)
            
            #print '--'.join([e['id'], e['name'], e['description'], str(sid)])
            charter = ''
            if sid:
                charter = self.get_sourceRepo(url, str(sid))
                charter = charter.replace('\n', ' ') if charter else ''
                charter = charter.replace('\t', ' ')
                charter = charter.replace('\r', ' ')
            furl = "https://radar.statcan.gc.ca/hackthons/"+e['id']
            l = [furl, e['name'], e['description'], 'en', last_modified, last_crawled, htags, 'hackathon']
            l = [ i.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ') if i else '' for i in l]
            hs.append(l)
        print hs
        return hs
    def process(self):
        print self.conf
        #last_crawled = datetime.now().isoformat()[:23]+'Z' #str(int(time.time()))
        last_crawled = datetime.utcnow().isoformat()[:23]+'Z' #str(int(time.time()))
        url = self.conf['start_links'][0]
        tags = self.get_tags(url)
        #self.get_sourceRepo(url, "7")
        #sys.exit(0)
        csv_data = []
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
              experimentTags { nodes {tagId} }
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
            print sid
            #print '--'.join([e['id'], e['name'], e['description'], str(sid)])
            charter = ''
            if sid:
                charter = self.get_sourceRepo(url, str(sid))
                charter = charter.replace('\n', ' ') if charter else ''
                charter = charter.replace('\t', ' ')
                charter = charter.replace('\r', ' ')
                #print charter
            etags = e['experimentTags']['nodes']
            etags = self.get_etags(tags, etags)
            furl = "https://radar.statcan.gc.ca/experiments/"+e['id']
            last_modified = e['updatedAt'][:23]+'Z'
            if not etags:
                etags = '[""]'
            else:
                etags = json.dumps(etags)
            
            l = [furl, e['name'], e['description'], 'en', last_modified, last_crawled, etags, 'experiment']
            l = [ i.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ') if i else '' for i in l]
            csv_data.append(l)
        hs = self.get_hackathons(tags)
        for h in hs:
            csv_data.append(h)
        write_csv(self.conf['output_file'], csv_data)

def read_config(filename):
    with open(filename) as f:
    # use safe_load instead load
        return yaml.safe_load(f)

def main():
    logging.basicConfig(format='%(asctime)s %(message)s',
                         filename='/tmp/radar_crawler.log', level=logging.INFO) #INFO, DEBUG
    confs = read_config(sys.argv[1])
    if len(sys.argv) >2:
        for conf in confs:
            data = conf.get(sys.argv[2], None)
            if not data: 
                continue
            craw = Crawler(data)
            craw.process()
            return
        return
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
