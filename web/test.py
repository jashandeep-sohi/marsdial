#!/usr/bin/env python2

import web
import psycopg2 as ps
from psycopg2.extras import RealDictCursor
import json

import bz2
import cPickle
import numpy as np
import cv2
import skimage.filter as skfilter

DEC2FLOAT = ps.extensions.new_type(
 ps.extensions.DECIMAL.values, 'DEC2FLOAT',
 lambda value, curs: float(value) if value is not None else None
)
ps.extensions.register_type(DEC2FLOAT)

conn = ps.connect(user='marsu', database='mars')

def unpackImg(img_bz2_pickle):
 return cPickle.loads(bz2.decompress(img_bz2_pickle))
 
def normalizeImg(img, mi=0., mx=1.):
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

def splitImg(row):
 img = unpackImg(row['image_py'])
 img_norm = normalizeImg(img)
 
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
 
 shadow_region = np.ma.masked_where(disk_region >= otsu_thresh, img_norm)
 light_region = np.ma.masked_where(disk_region < otsu_thresh, img_norm)
 
 img_png_r, img_png_buff = cv2.imencode('.png', (2**8 * disk_region).astype('uint8'))
 return img_png_buff

class Index(object):
 def GET(self):
  return web.template.frender('templates/index.html')()

class OpacityVsScatter(object):
 def GET(self):
  rcur = conn.cursor(cursor_factory=RealDictCursor)
  q_default_params = {
   'host_id': ['MER1',],
   'filter_id': ['L2',],
   'min_ltst_h': '11', 'min_ltst_m': '00', 'min_ltst_s': '00',
   'max_ltst_h': '13', 'max_ltst_m': '00', 'max_ltst_s': '00',
   'min_pixels': 200
  }
  q_params = web.input(**q_default_params)
  q_params['min_ltst'] = '{min_ltst_h}:{min_ltst_m}:{min_ltst_s}'.format(**q_params)
  q_params['max_ltst'] = '{max_ltst_h}:{max_ltst_m}:{max_ltst_s}'.format(**q_params)
  q = """
  SELECT DISTINCT ON(pds_headers_v.id)
   pds_headers_v.id,
   pds_headers_v.host_id,
   pds_headers_v.sol,
   pds_headers_v.ltst::text,
   pds_headers_v.filter_id,
   pds_headers_v.filter_wavelength,
   pds_headers_v.solar_longitude,
   pds_headers_v.radiance_scaling_factor,
   pds_headers_v.radiance_offset,
   atmos_opacities_v.atmos_opacity,
   phot_vals_disk1.shadow_mean,
   phot_vals_disk1.light_mean,
   phot_vals_disk1.shadow_std,
   phot_vals_disk1.light_std,
   phot_vals_disk1.shadow_pixels,
   phot_vals_disk1.light_pixels,
   (phot_vals_disk1.shadow_mean * pds_headers_v.radiance_scaling_factor) +
   pds_headers_v.radiance_offset as corrected_shadow_mean,
   (phot_vals_disk1.light_mean * pds_headers_v.radiance_scaling_factor) +
   pds_headers_v.radiance_offset as corrected_light_mean
  FROM
   phot_vals_disk1
   JOIN pds_headers_v USING(id)
   JOIN atmos_opacities_v USING(sol, host_id)
  WHERE
   pds_headers_v.filter_id = ANY(%(filter_id)s) AND
   pds_headers_v.host_id = ANY(%(host_id)s) AND
   pds_headers_v.ltst BETWEEN %(min_ltst)s AND %(max_ltst)s AND
   phot_vals_disk1.shadow_pixels > %(min_pixels)s AND
   phot_vals_disk1.light_pixels > %(min_pixels)s AND
   atmos_opacities_v.filter_id = 'R8' AND
   atmos_opacities_v.host_id = ANY(%(host_id)s)
  ORDER BY
   pds_headers_v.id, abs(extract(EPOCH FROM pds_headers_v.ltst-atmos_opacities_v.ltst));"""
  rcur.execute(q, dict(q_params))
  result = rcur.fetchall()
  web.header('Content-Type', 'application/json')
  return json.dumps(result, indent=3, separators=(',',': '), sort_keys=True)

class Images(object):
 def genImages(self):
  rcur = conn.cursor(cursor_factory=RealDictCursor)
  q_params = web.input()
  q = """
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
   JOIN ref_images ON(ref_images.id = image_regs.ref_id)
  WHERE
   pds_files.id = %(id)s;"""
  rcur.execute(q, q_params)
  row = rcur.fetchone()
  rcur.close()
  try:  
   img = unpackImg(row['image_py'])
   img_norm = normalizeImg(img)
   img_u8bit = (2**8 * img_norm).astype('uint8')
   img_color = cv2.applyColorMap(img_u8bit, cv2.COLORMAP_HSV)
   img_png_r, img_png_buff = cv2.imencode('.png', img_color)
  except Exception as e:
   raise e
  else:
   return buffer(img_png_buff)
 def GET(self):
  return self.genImages()
  
urls = (
 '/', 'Index',
 '/json/dataset/1', 'OpacityVsScatter',
 '/json/images', 'Images',
)
app = web.application(urls, locals())

if __name__ == '__main__':
 app.run()
