# -*- coding: utf-8 -*-

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

def append_csv(filename, rows):
    outf=open(filename, 'ab')
    writer = unicodecsv.writer(outf, delimiter='\t')

    for row in rows:
        writer.writerow(row)

def write_csv(filename, rows, header=None):
    outf=open(filename, 'wb')
    outf.write(codecs.BOM_UTF8)
    writer = unicodecsv.writer(outf, delimiter='\t')

    if header:
        writer.writerow(header)
    for row in rows:
        writer.writerow(row)

csv.field_size_limit(sys.maxsize)

def read_csv(filename):
    content=[]
    with open(filename) as f:
        f.read(3)
        reader = csv.reader(f, delimiter='\t')
        for x in reader:
            if x:
                content.append(x)
    return content

def read_jsonfile(filename):
    with open(filename) as jd:
        return json.load(jd)

def write_jsonfile(filename, data):
    with open(filename, 'w') as jd:
        json.dump(data, jd, indent=4)
