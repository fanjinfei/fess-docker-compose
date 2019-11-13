import ssl
def a(c, h):
    pass
ssl.match_hostname = a
#ssl.match_hostname = lambda cert, hostname: True
#ssl.https_verify_certificates(enable=False)

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
        print (data)
        try:
            r = requests.post(url=url, data=data, timeout=10)
        except:
            s = traceback.format_exc()
            print (url, sid, data, s)
            return None
        if r.status_code != requests.codes.ok:
            print (r)
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
            print (url, s)
            return None
        if r.status_code != requests.codes.ok:
            print ('get tags failed: ', r)
            return None
        source = json.loads(r.text)
        res = {}
        for node in source['data']['tags']['nodes']:
            res[node['id']] = node['name']
        print (res)
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
            print (r.text[-200:])
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
        print (hs)
        return hs
    def process(self):
        print (self.conf)
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
        print (data)
        r = requests.post(url=url, data=data, timeout=10)
        res = None
        if r.status_code == requests.codes.ok:
            print (r.text[-200:])
            res = json.loads(r.text)
        else:
            print ('Can not get data!')
            return
        for e in res['data']['experiments']['nodes']:
            sid = e['sourceRepositoryId']
            print (sid)
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
        for short_name, data in conf.items():
            print ('"'+short_name+'"')
            if not data.get('enabled', True):
                continue
            craw = Crawler(data)
            craw.process()
    return
def test(raw_cookie):
    from http.cookies import SimpleCookie
    pcookie = SimpleCookie()
    pcookie.load(raw_cookie)
    cookie = {}
    for p in pcookie.values():
        cookie[p.key] = p.coded_value
    #import pdb; pdb.set_trace()
    url = 'https://radar.statcan.gc.ca/api/'
    data = {  
       "variables":{  

       },
       "query":'''{ studies(orderBy: CREATED_AT_DESC) {
                      nodes {
                        ...StudyData
                      }
                    }
                 }
                fragment StudyData on Study {
                  id
                  name
                  description
                  type
                  createdBy
                  createdAt
                  updatedAt
                  sourceRepositoryId
                }
            '''
    }
    r = requests.post(url=url, data=data, timeout=10, cookies=cookie)
    print (r.text, r.status_code)
def parse_experiment_details(s):
    data = []
    return data
def dump_exp(raw_cookie):
    from http.cookies import SimpleCookie
    pcookie = SimpleCookie()
    pcookie.load(raw_cookie)
    cookie = {}
    for p in pcookie.values():
        cookie[p.key] = p.coded_value
    #import pdb; pdb.set_trace()
    url = 'https://radar.statcan.gc.ca/api/'
    data = {  
       "variables":{  
       },
       "query":'''{ studies(orderBy: CREATED_AT_DESC) {
                      nodes {
                        ...StudyData
                      }
                    }
                 }
                fragment StudyData on Study {
                  id
                  name
                  description
                  type
                  createdBy
                  createdAt
                  updatedAt
                  sourceRepositoryId
                }
            '''
    }
    details = { 
          "operationName":None,
           "variables":{"id":"322"},
          "query":"query ($id: BigInt!) {\n  studyById(id: $id) {\n    ...ExperimentWithTags\n    documents {\n      nodes {\n        ...DocumentData\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment ExperimentWithTags on Study {\n  ...StudyDataWithTags\n  ...ExperimentData\n  __typename\n}\n\nfragment ExperimentData on Study {\n  experiment {\n    id\n    conclusion\n    concludedAt\n    __typename\n  }\n  studyContributors {\n    nodes {\n      userId\n      studyId\n      user {\n        userProfile {\n          id\n          fullName\n          __typename\n        }\n        __typename\n      }\n      role {\n        id\n        roleName\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  studyContributorNames {\n    nodes {\n      id\n      studyId\n      name\n      role {\n        id\n        roleName\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment StudyDataWithTags on Study {\n  ...StudyData\n  ...StudyTags\n  __typename\n}\n\nfragment StudyData on Study {\n  id\n  name\n  description\n  type\n  createdBy\n  createdAt\n  updatedAt\n  visibility\n  isStatCan\n  sourceRepositoryId\n  numOfResolvedFlags\n  numOfFlags\n  userProfile {\n    id\n    firstName\n    lastName\n    fullName\n    email\n    field\n    __typename\n  }\n  flags {\n    nodes {\n      id\n      type\n      status\n      flagType {\n        type\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  studyTechnologiesTechnologies {\n    nodes {\n      id\n      name\n      category {\n        id\n        name\n        parentName\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment StudyTags on Study {\n  studyTagsTags {\n    nodes {\n      id\n      name\n      tagGroup {\n        id\n        name\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment DocumentData on Document {\n  id\n  name\n  content\n  visibility\n  position\n  studyId\n  contributors\n  createdAt\n  updatedAt\n  study {\n    id\n    type\n    name\n    createdBy\n    __typename\n  }\n  __typename\n}\n"
        }

    r = requests.post(url=url, data=data, timeout=10, cookies=cookie)
    if r.status_code != requests.codes.ok:
        print ('Failed to dump experiments')
    res = json.loads(r.text)
    data = []
    assert ( len(res['data']['studies']['nodes']) > 0)
    keys = res['data']['studies']['nodes'][0].keys()
    data.append( ([ key for key in keys]) )
    
    res_exp_details = []
    res_exp_details.append(['id', 'name', 'description', 'type', 'createBy', 'createAt', 'updateAt', 
                              'visibility', 'fullname', 'field', 'conclusion', 'concludedAt' ])
    for item in res['data']['studies']['nodes']:
        data.append(( [ item.get(key, "") for key in data[0] ] ))
        if item.get('type', '') != 'EXPERIMENT': continue
        eid = item.get("id")
        #if eid not in ['5', '97']: continue

        details['variables'] = json.dumps( { "id": "{0}".format(eid) })
        count = 5
        while count > 0:
            try:
                count -= 1
                r = requests.post(url=url, data=details, timeout=20, cookies=cookie)
                if r.status_code != requests.codes.ok:
                    print ('Failed to dump experiments details', eid)
                else:
                    info = json.loads(r.text)
                    info = info['data']['studyById']
                    res = []
                    for k in ['id', 'name', 'description', 'type', 'createdBy', 'createdAt', 'updatedAt', 
                              'visibility' ]:
                        res.append(info.get(k, ''))

                    user = info.get('userProfile', {} )
                    res.append(user.get('fullName', ''))
                    res.append(user.get('field', ''))

                    conclusion = info.get('experiment')
                    res.append(conclusion.get('conclusion', ''))
                    res.append(conclusion.get('concludedAt', ''))
                    
                    res_exp_details.append(res)
                    print('reading details of ', eid)
                    break
            except:
                import traceback
                traceback.print_exc()
                print("SSL error exc at ", eid)
    #data = list(filter(lambda x: x['type']=='EXPERIMENT', data))
    write_csv('/tmp/dump_radar.csv', data, delimiter=',')
    write_csv('/tmp/dump_experiments_details.csv', res_exp_details, delimiter=',')
    print ('Total: ', len(data), len(res_exp_details))

def test2():
    from requests_oauth2.services import GoogleClient
    google_auth = GoogleClient(
        client_id="your-google-client-id",
        client_secret="super-secret",
        redirect_uri="http://localhost:5000/google/oauth2callback",
    )
    authorization_url = google_auth.authorize_url(
        scope=["email"],
        response_type="code",
    )
    code = get_request_parameter("code") # this depends on your web framework!
    data = google_auth.get_token(
        code=code,
        grant_type="authorization_code",
    )
    session["access_token"] = data["access_token"]

if __name__ =='__main__':
    if sys.argv[1] =='test':
        test(sys.argv[2])
    elif sys.argv[1] =='dump_experiment':
        dump_exp(sys.argv[2])
    else:
        main()
    ''' CRAWL experiment details
{ 
   "operationName":null,
   "variables":{ 
      "id":"322"
   },
   "query":"query ($id: BigInt!) {\n  studyById(id: $id) {\n    ...ExperimentWithTags\n    documents {\n      nodes {\n        ...DocumentData\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment ExperimentWithTags on Study {\n  ...StudyDataWithTags\n  ...ExperimentData\n  __typename\n}\n\nfragment ExperimentData on Study {\n  experiment {\n    id\n    conclusion\n    concludedAt\n    __typename\n  }\n  studyContributors {\n    nodes {\n      userId\n      studyId\n      user {\n        userProfile {\n          id\n          fullName\n          __typename\n        }\n        __typename\n      }\n      role {\n        id\n        roleName\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  studyContributorNames {\n    nodes {\n      id\n      studyId\n      name\n      role {\n        id\n        roleName\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment StudyDataWithTags on Study {\n  ...StudyData\n  ...StudyTags\n  __typename\n}\n\nfragment StudyData on Study {\n  id\n  name\n  description\n  type\n  createdBy\n  createdAt\n  updatedAt\n  visibility\n  isStatCan\n  sourceRepositoryId\n  numOfResolvedFlags\n  numOfFlags\n  userProfile {\n    id\n    firstName\n    lastName\n    fullName\n    email\n    field\n    __typename\n  }\n  flags {\n    nodes {\n      id\n      type\n      status\n      flagType {\n        type\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  studyTechnologiesTechnologies {\n    nodes {\n      id\n      name\n      category {\n        id\n        name\n        parentName\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment StudyTags on Study {\n  studyTagsTags {\n    nodes {\n      id\n      name\n      tagGroup {\n        id\n        name\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment DocumentData on Document {\n  id\n  name\n  content\n  visibility\n  position\n  studyId\n  contributors\n  createdAt\n  updatedAt\n  study {\n    id\n    type\n    name\n    createdBy\n    __typename\n  }\n  __typename\n}\n"
}
''' 
    
    '''from oauthlib.oauth2 import LegacyApplicationClient
    from requests_oauthlib import OAuth2Session
    from oauthlib.oauth2 import BackendApplicationClient
    from requests.auth import HTTPBasicAuth
    client_id = '453270'
    client_secret = 'your_client_secret'
    client = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=client)
    #https://account.gccollab.ca/openid/authorize?client_id=453270&scope=openid%20email%20profile&response_type=code&redirect_uri=https%3A%2F%2Fradar.statcan.gc.ca%2Fauth%2Fcb&state=ps0-c_Dr2gJXu0T_g_9v2kIbbwX5FfQpv6wnu0icp1Q
    token = oauth.fetch_token(token_url='https://account.gccollab.ca/openid/authorize', client_id=client_id,
            client_secret=client_secret)
    #auth = HTTPBasicAuth(client_id, client_secret)
    #token = oauth.fetch_token(token_url='https://provider.com/oauth2/token', auth=auth) '''
    
