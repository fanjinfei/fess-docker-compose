import hashlib

import sys
import os
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

import logging

# These two lines enable debugging at httplib level (requests->urllib3->http.client)
# You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# The only thing missing will be the response.body which is not logged.
try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client
http_client.HTTPConnection.debuglevel = 1

# You must initialize logging, otherwise you'll not see debug output.
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

username = os.environ.get('ORCH_USERNAME', '') #windows set environ var, no quote for values
password = os.environ.get('ORCH_PASSWORD', '')
print (username, password)
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
        print (data)
        r = requests.post(url=url, data=data, timeout=10)
        if r.status_code != requests.codes.ok:
            print (r)
            return None
        source = json.loads(r.text)
        #import pdb; pdb.set_trace()
        #print source['data']['sourceRepositoryById']['webUrl']    
        return source['data']['sourceRepositoryById']['charter']

    def get_blog(self, url):
        login = 'http://localhost:5000/Login?returnurl=%2Fadmin'
        s = requests.Session()
        r = s.get('http://localhost:5000/admin', allow_redirects=False)
        
        print ('admin: ', s.cookies, r)
            
        #print (header, data)
        r = s.get(url=login)
        y = ' type="hidden" value="'
        x = r.text.find(y)
        if x != -1:
            x += len(y)
            veri_token = r.text[x: x+155]
        print ('get login: ', r, s.cookies)

        vtoken=s.cookies['.AspNetCore.Antiforgery.G3GvDPPzHoA']
        print ('cookie ', veri_token)
#   'Cookie': '.AspNetCore.Antiforgery.G3GvDPPzHoA='+vtoken,
        data = { 'UserName':username,
                  'RememberMe': 'false',
                 '__RequestVerificationToken': veri_token,
                 'Password':password}
        r = s.post(url=login, data=data, allow_redirects=False,  timeout=8)
        jar = s.cookies
        dj = dict(jar)
        oauth = dj['orchauth_Default']
        print ('login response: ', r)
        s.get(url='http://localhost:5000/admin', timeout=10)

        data = {
            "query": '{ blogPost { modifiedUtc publishedUtc  subtitle }}',
            #"variables": 'null'
        }
    
        header ={
            'Host': 'localhost:5000',
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0',
'Accept': 'application/json',
'Accept-Language': 'en-US,en;q=0.5',
'Accept-Encoding': 'gzip, deflate',
'Referer': 'http://localhost:5000/admin/graphql?query=%0A%7B%20blogPost%20%7B%20modifiedUtc%20publishedUtc%20%20subtitle%20%7D%20%7D%0A',
'content-type': 'application/json',
'Origin': 'http://localhost:5000',
'Content-Length': '97',
'Connection': 'keep-alive',
'Cookie': 'orchauth_Default='+oauth,
'Pragma': 'no-cache',
'Cache-Control': 'max-age=0, no-cache',
'Upgrade-Insecure-Requests': '1'
            }
        s.cookies.set('orchauth_Default', oauth)
        print ('data:', json.dumps(data))
        datas = '''{"query":"{blogPost {  createdUtc  modifiedUtc  publishedUtc\n  subtitle\n}\n}","variables":null}'''
        r = s.post(url=url, data=json.dumps(data), headers=header,  timeout=10)
        if r.status_code != requests.codes.ok:
            print (r)
            return None
        source = json.loads(r.text)
        #import pdb; pdb.set_trace()
        print (source   )
        #return source['data']['sourceRepositoryById']['charter']

    def process(self):
        print (self.conf)
        url = self.conf['start_links'][0]
        #self.get_sourceRepo(url, "7")
        self.get_blog(url)
        sys.exit(0)
        
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
        print (data)
        r = requests.post(url=url, data=data, timeout=10)
        res = None
        if r.status_code == requests.codes.ok:
            print (r.text[-200:])
            res = json.loads(r.text)
        if not res: return
        for e in res['data']['experiments']['nodes']:
            sid = e['sourceRepositoryId']
            print ('--'.join([e['id'], e['name'], e['description'], str(sid)]))
            if not sid: continue
            charter = self.get_sourceRepo(url, str(sid))
            charter = charter.replace('\n', ' ') if charter else ''
            charter = charter.replace('\t', ' ')
            charter = charter.replace('\r', ' ')
            print (charter)


def read_config(filename):
    with open(filename) as f:
    # use safe_load instead load
        return yaml.safe_load(f)

def main():
   # logging.basicConfig(format='%(asctime)s %(message)s',
   #                      filename='/tmp/radar_crawler.log', level=logging.INFO) #INFO, DEBUG
    confs = read_config(sys.argv[1])
    for conf in confs:
        for short_name, data in conf.items():
            print ('"'+short_name+'"')
            if not data.get('enabled', True):
                continue
            craw = Crawler(data)
            craw.process()
    return
    
if sys.argv[1] =='test':
    test()
else:
    main()
