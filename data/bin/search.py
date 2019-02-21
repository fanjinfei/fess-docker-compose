# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
from flask import make_response, current_app
from flask import render_template, redirect, g, url_for, abort
from flask import send_from_directory
from flask import Response
from flask_babel import Babel
from flask_paginate import Pagination, get_page_parameter
from flask_compress import Compress
#from flask_sslify import SSLify
import mimetypes
import urllib
import requests
import json
import sys,os
import re
import markupsafe
from base64 import b64encode
from datetime import timedelta
from functools import update_wrapper
import logging
from logging.handlers import RotatingFileHandler

import pprint

static_dir = './static/'
mimetypes.init()
mimetypes.add_type('image/svg+xml', '.svg')

'export ECN_CONFIG=http://XXX.ca:9601'
#print 'sys argv ', sys.argv, os.environ['ECN_CONFIG']

#// url:'https://www120.statcan.gc.ca/stcsr/en/cm1/cls?fq=ds%3A102noc2016&start=0&showSum=show&q=orign&wt=json'
end_point = 'http://localhost:8080'
#end_point = 'https://innovation-search-production.inno.cloud.statcan.ca'


app = Flask(__name__, template_folder="./")
Compress(app)
#SSLify(app)
handler = RotatingFileHandler('/tmp/search.log', maxBytes=1000000, backupCount=1)
handler.setLevel(logging.DEBUG)
app.logger.setLevel(logging.DEBUG)
app.logger.addHandler(handler)
logger = logging.getLogger('werkzeug')
logger.addHandler(handler)

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

@app.before_request
def before():
    if request.view_args and 'lang_code' in request.view_args:
        if request.view_args['lang_code'] not in ('fr', 'en'):
            return abort(404)
            #g.current_lang = 'en'
        else:
          g.current_lang = request.view_args['lang_code']
          request.view_args.pop('lang_code')

@app.after_request
def add_header(response):
#    response.cache_control.max_age = 300
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

#@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404
    
def _send_static(filename):
    mtype, _ = mimetypes.guess_type(filename)
    return send_from_directory(static_dir, filename, mimetype=mtype)

#@app.route('/<string:page_name>/')
@app.route('/static/<string:page_name>')
def static_page(page_name):
    #response.headers['Content-Security-Policy'] = "default-src 'self'"
    return _send_static(page_name)
    #return render_template('%s' % page_name)

'''
@app.route('/js/<string:page_name>')
def js_page(page_name):
    #Force redirect to https, another port
    if False and request.url.startswith('http://'):
        return redirect(request.url.replace('http', 'https', 1)
                        .replace('8002', '8001', 1))
    return _send_static(page_name)
'''

date_range = {
    "timestamp:[now-1d/d TO *]":[0,'Past 24 Hours'],
    "timestamp:[now-7d/d TO *]":[1,'Past Week'],
    "timestamp:[now-30d/d TO *]":[2, 'Past Month'],
    "timestamp:[now-1y/d TO *]":[3, 'Past Year'],
    "timestamp:[* TO now-1y-1d/d]":[4, 'One Year Older'],
}

def _get_search_post(q, start_page=1, page_size=20, labels=None, burl=None, lang='en', sort='', ex_q=''):
    start = (start_page-1)*page_size
    if not burl: burl=base_url
    if burl[-1] == '?': burl = burl[:-1]

    payload= {'q':q,
              'start':start,
              'num':page_size,
              'lang':lang,
              'sort':sort,
              'facet.query':list(date_range.keys())
            }
    if labels:
        payload['fields.label'] = labels
    if ex_q:
        payload['ex_q'] = ex_q

    print (burl, payload)
    user_agent = {'User-agent': 'statcan search'}
    r = requests.post(url=burl, headers=user_agent, data=payload, timeout=3)
    if r.status_code == requests.codes.ok:
        print r.text[-200:]
        return r.text
    else:
        return None

def qfilter(val):
    r = []
    for c in val:
        if c.isalnum() or c in ['-', '\'', '"', '+', '*', ':']:
            r.append(c)
        else:
            r.append(' ')
    return u''.join(r) 

@app.route("/api/<lang_code>/stc_search", methods=['GET'])
@crossdomain(origin='*')
def stc_search():
    qval = request.args.get('q')
    lang = request.args.get('lang')
    sort = '' # request.args.get('sort')
    ex_q = request.args.get('ex_q', '')

    page = request.args.get('start', 1, type=int) #rows
    if page <1: page=1
    rows = request.args.get('rows', 20, type=int) #rows
    if (rows>1000):
        rows = 1000
    request.get_json()
    #print (qval, request.get_json(), request.data, request.args)

    res = None
    data = {}
    data['start'] = 0
    data['total'] = 0
    data['docs'] = []
    labels = []
    if qval:
      try:
        res = _get_search_post(qfilter(qval), page, 20, labels,
                          end_point+'/json/', lang, sort, ex_q)
        if res:
            res = json.loads(res)
            res = res['response']
            
      except:
        #TODO: show server error message
        import traceback
        traceback.print_exc()
        print "all servers are down"
        #return "service unavailable", 503
#      return "service unavailable", 503
      if res:
            total,start = res.get('record_count', 0), res.get('start_record_number', 0)
            print 'total', total, page, start, rows
            data['total'] = total
            data['start'] = start

            #mapping for this solr core
            for doc in res['result']:
                data['docs'].append(doc)
            res['result']= None
            print res
    response = jsonify(data)

    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/<path:path>', methods=['POST', 'GET'])
def proxy(path):
  cookies = request.cookies
  dj = dict(cookies)
  s = requests.Session()
  try:
      if request.method == 'GET':
        params = urllib.urlencode(request.args)
        res = s.get('{end_point}/{path}?{query}'.format(end_point=end_point, path=path, query=params), cookies=dj, timeout=3)
        if "NotfoundAction_index_Form" in res.content or res.status_code != requests.codes.ok:
            return "Not found", 404
        response = make_response(res.content, res.status_code)
        if res.headers.get('Content-type', None):
          response.headers['Content-type'] = res.headers['Content-type']
        for k,v in dict(s.cookies).items():
            response.set_cookie(k,v)
        return response
      else:
        data = request.form
        res =  s.post('{end_point}/{path}'.format(end_point=end_point, path=path), data=data, cookies=dj, timeout=3)
        response = make_response(res.content, 200)
        for k,v in dict(s.cookies).items():
            response.set_cookie(k,v)
        return response
  except:
        import traceback
        traceback.print_exc()
        return  "Not found", 404

def test():
    print _get_search_post('data', 1, 20, '',
                          end_point+'/json/', 'en', '', '')    
    sys.exit(0)

if __name__ == "__main__":
    #test()
    from gevent.pywsgi import WSGIServer
    http_server = WSGIServer(('0.0.0.0', 8002), app, log=app.logger)
    http_server.serve_forever()
else:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

