#!/usr/bin/env python2

import os
import sys
import gzip
import numpy as np
import json
import cPickle
import bz2
import psycopg2 as ps

def parseHeaders(f_content):
 t = list()
 for line in f_content.splitlines(True):
  if line == b'END\r\n':
   break
  line = str(line).strip()
  if line.startswith('/*') and line.endswith('*/'):
   continue
  if ' = ' in line:
   t.append( '='.join([x.strip() for x in line.split('=')]))
  elif line:
   p = t.pop()
   p= p + ' ' + line
   t.append(p)
 d = dict()
 it = iter(t) 
 while True:
  try: e = it.next()
  except:break
  k,v = e.split('=') 
  if k in ('OBJECT', 'GROUP'):
   d2 = dict()
   k1, v1 = it.next().split('=')
   while k1 != 'END_'+k:
    d2[k1.lower()] = v1.strip('"')
    k1, v1 = it.next().split('=')
   d[v.lower()] = d2
  else: d[k.lower()] = v.strip('"')
 return d


def parseImage(f_content, h):
 f_bytearray = bytearray(f_content)
 width = int(h['image']['line_samples'])
 height = int(h['image']['lines'])
 image_pointer = int(h['^image'])
 record_bytes = int(h['record_bytes'])
 imgLoc = (image_pointer-1)*record_bytes
 img_dt = np.dtype( ('>i2', width), ('>i2', height))
 img = np.frombuffer(f_bytearray[imgLoc:], dtype=img_dt).byteswap().newbyteorder()
 return img

def buildPDSFilesTable(conn, directory):
 cur = conn.cursor()
 wq = """INSERT INTO pds_files (id, headers_json, image_py) VALUES (%s, %s, %s); """
 for f_name in os.listdir(directory):
  if not f_name.lower().endswith('.img.gz'):
   continue
  f_path = os.path.join(directory, f_name)
  with gzip.open(f_path) as f:
   f_content = f.read()
   headers_dict = parseHeaders(f_content)
   headers_json = json.dumps(headers_dict)
   img = parseImage(f_content, headers_dict)
   imgs = bz2.compress(cPickle.dumps(img, -1), 9)
   p_id = headers_dict['product_id']
   print p_id
   cur.execute(wq, (p_id, headers_json, buffer(imgs)) )
 conn.commit()

if __name__ == '__main__':
 conn = ps.connect(user='mars', database='mars')
 try:
  directory = sys.argv[1]
 except:
  raise Exception('Need a directory argument to look for files.')
 buildPDSFilesTable(conn, directory)
