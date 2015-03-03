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


def checkAlignment(conn):
 rcur = conn.cursor('images', cursor_factory=RealDictCursor)
 rq = """
 SELECT
  image_regs.id,
  image_regs.r,
  image_regs.dx,
  image_regs.dy,
  pds_files.image_py,
  pds_headers_v.host_id,
  pds_headers_v.filter_id
 FROM
  image_regs
  JOIN pds_headers_v USING(id)
  JOIN pds_files USING(id)
 ORDER BY
  image_regs.r
 LIMIT 200;"""
 refImages = getRefImages(conn)
 rcur.execute(rq)
 for row in rcur:
  ref_row = refImages[row['host_id'], row['filter_id']]
  ref_img = normalize(unpackImg(ref_row['image_py']))
  img = normalize(unpackImg(row['image_py']))
  dx, dy = row['dx'], row['dy']
  print row['id'], row['r'], dx, dy
  
  shifted_img = ndimage.interpolation.shift(img, (-dy,-dx))
  mixed_img = ref_img/2 + shifted_img/2
  
  cv2.namedWindow('img', flags=cv2.WINDOW_NORMAL)
  cv2.imshow('img', (255*mixed_img).astype('uint8'))
  cv2.waitKey()

if __name__ == '__main__':
 conn = ps.connect(user='mars', database='mars')
 checkAlignment(conn)
