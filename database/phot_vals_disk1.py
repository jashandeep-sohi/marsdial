#!/usr/bin/env python2

import bz2
import cPickle
import numpy as np
import cv2
from psycopg2.extras import RealDictCursor
import psycopg2 as ps
import skimage.filter as skfilter


DEC2FLOAT = ps.extensions.new_type(
 ps.extensions.DECIMAL.values,
 'DEC2FLOAT',
 lambda value, curs: float(value) if value is not None else None
)
ps.extensions.register_type(DEC2FLOAT)

def unpackImg(img_bz2_pickle):
 return cPickle.loads(bz2.decompress(img_bz2_pickle))

def normalize(img, mi=0., mx=1.):
 return mi + (mx-mi) * (img-img.min()) / (img.max()-img.min())

def ellipse2Poly(rrect, center_corr=(0,0), size_corr=(0,0), angle_corr=0):
 center, size, angle = np.array(rrect)
 size = np.array(size)/2.
 center_int = np.rint( center + np.array(center_corr)).astype('int')
 size_int = np.rint( size + np.array(size_corr)).astype('int')
 angle_int = np.rint( angle + angle_corr).astype('int')
 return cv2.ellipse2Poly(tuple(center_int), tuple(size_int), angle_int, 0, 360, 1)

def rrect2Poly(rrect, center_corr=(0,0), size_corr=(0,0), angle_corr=0):
 center, size, angle = np.array(rrect)
 center = center + np.array(center_corr)
 a, b = size = size + np.array(size_corr)
 angle = angle + angle_corr
 rads = np.radians(angle)
 x = np.array([a, -a, -a, a])/2.
 y = np.array([b, b, -a, -a])/2.
 
 x_p = x*np.cos(rads) - y*np.sin(rads)
 y_p = x*np.sin(rads) + y*np.cos(rads)
 
 return center + np.array([x_p,y_p]).T
 
def measureValues(conn):
 rcur = conn.cursor('images', cursor_factory=RealDictCursor)
 wcur = conn.cursor()
 
 wq = """
 INSERT INTO phot_vals_disk1(
  id,
  shadow_mean,
  light_mean,
  shadow_std,
  light_std,
  shadow_pixels,
  light_pixels
 )
 VALUES(
  %(id)s,
  %(shadow_mean)s,
  %(light_mean)s,
  %(shadow_std)s,
  %(light_std)s,
  %(shadow_pixels)s,
  %(light_pixels)s
 );"""
 
 rq = """
 SELECT
  pds_files.id,
  pds_files.image_py,
  image_regs.dx,
  image_regs.dy,
  ref_images.elps_outer,
  ref_images.elps_middle,
  ref_images.elps_earth,
  ref_images.elps_mars,
  ref_images.poly_post
 FROM
  image_regs
  JOIN pds_files USING(id)
  JOIN ref_images ON(ref_images.id = image_regs.ref_id);"""
 rcur.execute(rq)
  
 for i,row in enumerate(rcur):
  print i,row['id']
  img = unpackImg(row['image_py'])
  img_norm = normalize(img)
  
  dx, dy = row['dx'], row['dy']
  dx_int, dy_int = np.rint( [row['dx'], row['dy'] ]).astype('int')
  
  elps_outer_poly = ellipse2Poly(row['elps_outer'], (dx, dy), (-3,-3))
  elps_middle_poly = ellipse2Poly(row['elps_middle'], (dx, dy), (3, 3))
  elps_earth_poly = ellipse2Poly(row['elps_earth'], (dx, dy))
  elps_mars_poly = ellipse2Poly(row['elps_mars'], (dx, dy), (2,2))
  
  post_rrect = cv2.minAreaRect(np.array(row['poly_post']))
  post_rrect_poly = np.rint(rrect2Poly(post_rrect, (dx, dy))).astype('int')
  
  disk_mask = np.ones_like(img_norm)
  cv2.fillPoly(disk_mask, [elps_outer_poly, elps_middle_poly], 0)
  cv2.fillPoly(disk_mask, [elps_mars_poly], 1)
  cv2.fillPoly(disk_mask, [elps_earth_poly], 1)
  cv2.fillPoly(disk_mask, [post_rrect_poly], 1)
  
  disk_region = np.ma.array(img_norm, mask=disk_mask)
  otsu_thresh = skfilter.threshold_otsu(disk_region.filled(0))
  
  shadow_region = np.ma.masked_where(disk_region >= otsu_thresh, img)
  light_region = np.ma.masked_where(disk_region < otsu_thresh, img)
  
  shadow_count = shadow_region.count()
  light_count = light_region.count()
  
  if shadow_count > 0:
   shadow_mean, shadow_std = shadow_region.mean(), shadow_region.std()
  else:
   shadow_mean, shadow_std = float('nan'), float('nan')
   
  if light_count > 0:
   light_mean, light_std = light_region.mean(), light_region.std()
  else:
   light_mean, light_std = float('nan'), float('nan')
   
  values = {
   'id': row['id'],
   'shadow_mean': shadow_mean,
   'light_mean': light_mean,
   'shadow_std': shadow_std,
   'light_std': light_std,
   'shadow_pixels': shadow_count,
   'light_pixels': light_count,
  }
  wcur.execute(wq, values)
 conn.commit()

if __name__ == '__main__':
 conn = ps.connect(user='mars', database='mars')
 measureValues(conn)
