#!/usr/bin/env python2

import bz2
import cPickle
import cv2
import numpy as np
from psycopg2.extras import RealDictCursor
import psycopg2 as ps
import scipy.ndimage as ndimage

DEC2FLOAT = ps.extensions.new_type(
 ps.extensions.DECIMAL.values,
 'DEC2FLOAT',
 lambda value,
 curs: float(value) if value is not None else None
)
ps.extensions.register_type(DEC2FLOAT)

def unpackImg(img_bz2_pickle):
 return cPickle.loads(bz2.decompress(img_bz2_pickle))

def normalize(img, mi=0., mx=1.):
 return mi + (mx-mi) * (img-img.min()) / (img.max()-img.min())

def canny(img, t1=1, t2=1, aS=3):
 return cv2.Canny(img, t1, t2, apertureSize=aS, L2gradient=True)
 
def getRefImages(conn):
 rcur = conn.cursor('ref_images', cursor_factory=RealDictCursor)
 rq = """
 SELECT DISTINCT ON(pds_headers_v.host_id, pds_headers_v.filter_id)
  ref_images.id,
  pds_headers_v.host_id,
  pds_headers_v.filter_id,
  pds_files.image_py
 FROM
  ref_images
  JOIN pds_headers_v USING(id)
  JOIN pds_files USING(id);"""
 rcur.execute(rq)
 d = {(row['host_id'],row['filter_id']): row for row in rcur }
 rcur.close()
 return d

def registerImages(conn):
 rcur = conn.cursor('images', cursor_factory=RealDictCursor)
 wcur = conn.cursor()
 
 wq = """
 INSERT INTO image_regs (
  id,
  r,
  dx,
  dy,
  ref_id
 )
 VALUES (
  %(id)s,
  %(r)s,
  %(dx)s,
  %(dy)s,
  %(ref_id)s
 );"""
 
 rq = """
 SELECT
  pds_files.id,
  pds_headers_v.host_id,
  pds_headers_v.filter_id,
  pds_headers_v.radiance_offset,
  pds_headers_v.radiance_scaling_factor,
  pds_files.image_py
 FROM
  pds_headers_v
  JOIN pds_files USING(id)
 WHERE
  pds_headers_v.img_width = 320 AND
  pds_headers_v.img_height = 272;""";
 
 refImages = getRefImages(conn)
 rcur.execute(rq)
 for i,row in enumerate(rcur):
  ref_row = refImages[row['host_id'], row['filter_id']]
  ref_img = unpackImg(ref_row['image_py'])
  img = unpackImg(row['image_py'])
  
  ref_img_uint8 = np.rint(255 * normalize(ref_img)).astype('uint8')
  img_uint8 = np.rint(255 * normalize(img)).astype('uint8')
  
  ref_img_canny = canny(ref_img_uint8, 26, 51)
  img_canny = canny(img_uint8, 26, 51)
  
  h_wnd = cv2.createHanningWindow(ref_img.shape[::-1], cv2.CV_32F)
  (dx,dy), r = cv2.phaseCorrelateRes(ref_img_canny.astype('float32'), img_canny.astype('float32'), h_wnd)
  
  values = {
   'id': row['id'],
   'ref_id': ref_row['id'],
   'r': r,
   'dx': dx,
   'dy': dy,
  }
  print i,row['id']
  wcur.execute(wq, values)
 conn.commit()

if __name__ == '__main__':
 conn = ps.connect(user='mars', database='mars')
 registerImages(conn)
 
