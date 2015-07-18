#!/usr/bin/python2

import cv2
import psycopg2 as ps
from psycopg2.extras import RealDictCursor
import numpy as np
import json
from scipy.ndimage.interpolation import shift

def Main():
 markRoi()
 
def markRoi():
 rconn = ps.connect(user='marsu', database='mars')
 wconn = ps.connect(user='mars', database='mars')
 
 rcur = rconn.cursor(cursor_factory=RealDictCursor)
 rq = "SELECT png_8bit, id, host_id, filter_name FROM rawimages JOIN pdsheaders USING(id) WHERE host_id = 'MER1' ORDER BY sol DESC, ltst DESC LIMIT 100;"
 rcur.execute(rq)
 
 for row in rcur:
  print row['host_id'], row['filter_name']
  img = cv2.imdecode(np.frombuffer(row['png_8bit'], dtype='uint8'), -1)
  cv2.namedWindow('img', flags=cv2.WINDOW_NORMAL)
  cv2.imshow('img', img)
  
  key = -1
  while True:
   if key % 256 == 27 or key == 1048686: break
   if key == 1048586:
    roi1 = poly(scharr8bit(img), 'Mark ROI #1')
    markRoiOthers(rconn, wconn, img, roi1)
   key = cv2.waitKey()
  if key % 256 == 27: break

def markRoiOthers(rconn, wconn, r_img, roi1):
 wcur = wconn.cursor()
 wq = "UPDATE ref_images SET poly_roi1=%s WHERE id=%s;"
 
 rcur = rconn.cursor(cursor_factory=RealDictCursor)
 rq = "SELECT png_8bit, id, host_id, filter_name FROM rawimages JOIN ref_images USING(id) JOIN pdsheaders USING(id) ORDER BY host_id,filter_name;"
 
 cv2.namedWindow('Align Image', flags=cv2.WINDOW_NORMAL)
 cv2.namedWindow('Align Poly', flags=cv2.WINDOW_NORMAL)
 
 rcur.execute(rq)
 shift_x, shift_y = 0, 0
 for row in rcur:
  print row['host_id'], row['filter_name']
  img = cv2.imdecode(np.frombuffer(row['png_8bit'], dtype='uint8'), -1)
  key = -1
  while True:
   dx, dy = 0, 0
   if key == 1113938: dy = dy - 1
   if key == 1376082: dy = dy - 5
   if key == 1113940: dy = dy + 1
   if key == 1376084: dy = dy + 5
   if key == 1113937: dx = dx - 1
   if key == 1376081: dx = dx - 5
   if key == 1113939: dx = dx + 1
   if key == 1376083: dx = dx + 5
   if key % 256 == 27 or key == 1048686: break
   if key == 1048691:
    data = (json.dumps(roi1), row['id'])
    try:
     wcur.execute(wq, data)
     wconn.commit()
    except Exception as e: print e
    else: print 'Updated', row['id']
   pimg = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
   shift_x, shift_y = shift_x+dx, shift_y+dy
   
   shifted_img_scharr = scharr8bit(img)
   r_img_scharr = scharr8bit( shift(r_img, (shift_y, shift_x)) )
   cv2.imshow('Align Image', cv2.addWeighted(shifted_img_scharr, .5, r_img_scharr, .5, 0) )
   
   adjustP = lambda poly: [ [x+dx, y+dy] for x,y in poly ]
   roi1 = adjustP(roi1)
   if roi1: cv2.polylines(pimg, [np.array(roi1).reshape(len(roi1), 1, 2)], isClosed=True, color=(255, 0, 0, 1))
   cv2.imshow('Align Poly', pimg)
   
   key = cv2.waitKey()
  if key % 256 == 27: break
 cv2.destroyWindow('Align Poly')
 cv2.destroyWindow('Align Image')

def alignOthers(rconn, wconn, r_img, (e1, e2, ee, em, pe, pm, pp, proi1)):
 cv2.namedWindow('Align Ellipses', flags=cv2.WINDOW_NORMAL)
 cv2.namedWindow('Align Polygons', flags=cv2.WINDOW_NORMAL)
 cv2.namedWindow('Align Image', flags=cv2.WINDOW_NORMAL)
 
 rq = "SELECT png_8bit, id, host_id, filter_name FROM rawimages JOIN ref_images USING(id) JOIN pdsheaders USING(id) ORDER BY host_id, filter_name;"
 rcur = rconn.cursor(cursor_factory=RealDictCursor)
 rcur.execute(rq)
 
 wq = "UPDATE ref_images SET elps_outer=%s,elps_middle=%s,elps_earth=%s,elps_mars=%s,poly_roi1=%s,poly_earth=%s,poly_mars=%s,poly_post=%s WHERE id=%s;"
 wcur = wconn.cursor()
 
 shift_x, shift_y = 0, 0
 
 for row in rcur:
  print row['host_id'], row['filter_name']
  img = cv2.imdecode(np.frombuffer(row['png_8bit'], dtype='uint8'), -1)
  key = -1
  while True:
   dx, dy = 0, 0
   if key == 1113938: dy = dy - 1
   if key == 1376082: dy = dy - 5
   if key == 1113940: dy = dy + 1
   if key == 1376084: dy = dy + 5
   if key == 1113937: dx = dx - 1
   if key == 1376081: dx = dx - 5
   if key == 1113939: dx = dx + 1
   if key == 1376083: dx = dx + 5
   if key % 256 == 27 or key == 1048686: break
   if key == 1048691:
    data = (json.dumps(e1), json.dumps(e2), json.dumps(ee), json.dumps(em), json.dumps(proi1), json.dumps(pe), json.dumps(pm), json.dumps(pp), row['id'])
    try:
     wcur.execute(wq, data)
     wconn.commit()
    except Exception as e: print e
    else: print 'Updated', row['id']
    
   eimg = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
   pimg = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
   shift_x, shift_y = shift_x+dx, shift_y+dy
   
   shifted_img_scharr = scharr8bit(img)
   r_img_scharr = scharr8bit( shift(r_img, (shift_y, shift_x)) )
      
   cv2.imshow('Align Image', cv2.addWeighted(shifted_img_scharr, .5, r_img_scharr, .5, 0) )
   
   adjustE = lambda elp_c, elp_ab, elp_an: ( (elp_c[0]+dx, elp_c[1]+dy), elp_ab, elp_an )
   adjustP = lambda poly: [ [x+dx, y+dy] for x,y in poly ]
   
   e1 = adjustE(*e1)
   e2 = adjustE(*e2)
   ee = adjustE(*ee)
   em = adjustE(*em)
   proi1 = adjustP(proi1)
   pe = adjustP(pe)
   pm = adjustP(pm)
   pp = adjustP(pp)
   
   cv2.ellipse(eimg, tuple(e1), color=(0,255, 0, 1))
   cv2.ellipse(eimg, tuple(e2), color=(0,255, 0, 1))
   cv2.ellipse(eimg, tuple(ee), color=(0,255, 0, 1))
   cv2.ellipse(eimg, tuple(em), color=(0,255, 0, 1))
   cv2.imshow('Align Ellipses', eimg)
   
   if proi1: cv2.polylines(pimg, [np.array(proi1).reshape(len(proi1), 1, 2)], isClosed=True, color=(255, 0, 0, 1))
   if pe: cv2.polylines(pimg, [np.array(pe).reshape(len(pe), 1, 2)], isClosed=True, color=(255, 0, 0, 1))
   if pm: cv2.polylines(pimg, [np.array(pm).reshape(len(pm), 1, 2)], isClosed=True, color=(255, 0, 0, 1))
   if pp: cv2.polylines(pimg, [np.array(pp).reshape(len(pp), 1, 2)], isClosed=True, color=(255, 0, 0, 1))
   cv2.imshow('Align Polygons', pimg)
   key = cv2.waitKey()
  if key % 256 == 27: break
  
 cv2.destroyWindow('Align Ellipses')
 cv2.destroyWindow('Align Polygons')
 cv2.destroyWindow('Align Image')

def editImages():
 rconn = ps.connect(user='marsu', database='mars', sslmode='require')
 wconn = ps.connect(user='mars', database='mars', sslmode='require')
 rquery = "SELECT ref_images.*, png_8bit, host_id, filter_name FROM ref_images JOIN rawimages USING(id) JOIN pdsheaders USING(id) ORDER BY host_id,filter_name;"
 rcur = rconn.cursor(cursor_factory=RealDictCursor)
 wcur = wconn.cursor()
 rcur.execute(rquery)
 
 for row in rcur:
  print row['id'], row['host_id'], row['filter_name']
  e1, e2, ee, em = json.loads(row['elps_outer']), json.loads(row['elps_middle']), json.loads(row['elps_earth']), json.loads(row['elps_mars'])
  pe, pm, pp, proi1 = json.loads(row['poly_earth']), json.loads(row['poly_mars']), json.loads(row['poly_post']), json.loads(row['poly_roi1'])
  img = cv2.imdecode(np.frombuffer(row['png_8bit'], dtype='uint8'), -1)
  cv2.namedWindow('img', flags=cv2.WINDOW_NORMAL)
  cv2.imshow('img', img)
  cv2.namedWindow('E', flags=cv2.WINDOW_NORMAL)
  cv2.namedWindow('P', flags=cv2.WINDOW_NORMAL)
  
  key = -1
  while True:
   eimg = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
   pimg = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
   if key % 256 == 27 or key == 1048686: break
   if key == 1048691:
    wquery = "UPDATE ref_images SET elps_outer=%s,elps_middle=%s,elps_earth=%s,elps_mars=%s,poly_roi1=%s,poly_earth=%s,poly_mars=%s,poly_post=%s WHERE id=%s;"
    data = (json.dumps(e1), json.dumps(e2), json.dumps(ee), json.dumps(em), json.dumps(proi1), json.dumps(pe), json.dumps(pm), json.dumps(pp), row['id'])
    try:
     wcur.execute(wquery, data)
     wconn.commit()
    except Exception as e: print e
    else: print 'Updated', row['id']
   if key == 1048586:
    e1_new = ellipse(img, 'Mark Outer Ellipse')
    e2_new = ellipse(img, 'Mark Middle Ellipse')
    ee_new = ellipse(img, 'Mark Earth Ellipse')
    em_new = ellipse(img, 'Mark Mars Ellipse')
    proi1_new = poly(scharr8bit(img), 'Mark ROI #1')
    pe_new = poly(img, 'Mark Earth Polygon')
    pm_new = poly(img, 'Mark Mars Polygon')
    pp_new = poly(img, 'Mark Post Polygon')
    
    if e1_new: e1 = e1_new
    if e2_new: e2 = e2_new
    if ee_new: ee = ee_new
    if em_new: em = em_new
    if proi1_new: proi1 = proi1_new
    if pe_new: pe = pe_new
    if pm_new: pm = pm_new
    if pp_new: pp = pp_new
   if key == 1048687:
    d = e1, e2, ee, em, pe, pm, pp, proi1
    alignOthers(rconn, wconn, img, d)
    
   cv2.ellipse(eimg, tuple(e1), color=(0,255, 0, 1))
   cv2.ellipse(eimg, tuple(e2), color=(0,255, 0, 1))
   cv2.ellipse(eimg, tuple(ee), color=(0,255, 0, 1))
   cv2.ellipse(eimg, tuple(em), color=(0,255, 0, 1))
   cv2.imshow('E', eimg)
   
   if proi1: cv2.polylines(pimg, [np.array(proi1).reshape(len(proi1), 1, 2)], isClosed=True, color=(255, 0, 0, 1))
   if pe: cv2.polylines(pimg, [np.array(pe).reshape(len(pe), 1, 2)], isClosed=True, color=(255, 0, 0, 1))
   if pm: cv2.polylines(pimg, [np.array(pm).reshape(len(pm), 1, 2)], isClosed=True, color=(255, 0, 0, 1))
   if pp: cv2.polylines(pimg, [np.array(pp).reshape(len(pp), 1, 2)], isClosed=True, color=(255, 0, 0, 1))
   cv2.imshow('P', pimg)
   key = cv2.waitKey()
   
  if key % 256 == 27: break


def addImages():
 rconn = ps.connect(user='marsu', database='mars', sslmode='require')
 wconn = ps.connect(user='mars', database='mars', sslmode='require')
 
 rquery = "SELECT png_8bit, id, filter_name FROM pdsheaders JOIN rawimages USING(id) WHERE ARRAY[img_width, img_height]='{320,272}' AND host_id='MER2' AND filter_name='PANCAM_R7_1001NM' ORDER BY sol,ltst LIMIT 150;"
 wquery = "INSERT INTO ref_images (id, elps_outer, elps_middle, elps_earth, elps_mars, poly_roi1, poly_earth, poly_mars, poly_post) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
 
 rcur = rconn.cursor()
 wcur = wconn.cursor()
 rcur.execute(rquery)
 
 for row in rcur:
  img = cv2.imdecode(np.frombuffer(row[0], dtype='uint8'), -1)
  ident = row[1]
  fname = row[2]
  print ident, fname
  cv2.namedWindow('img', flags=cv2.WINDOW_NORMAL)
  cv2.imshow('img', img)
  
  cv2.namedWindow('edeges', flags=cv2.WINDOW_NORMAL)
  cv2.imshow('edeges', canny(img))
  
  while True:
   key = cv2.waitKey()
   if key % 256 == 27 or key == 1048686: break
   if key == 1048586:
    e1 = ellipse(img, 'Mark Outer Ellipse')
    e2 = ellipse(img, 'Mark Inner Ellipse')
    ee = ellipse(img, 'Mark Earth Ellipse')
    em = ellipse(img, 'Mark Mars Ellipse')
    roi1 = poly(img, 'Mark Disk ROI')
    earth_p = poly(img, 'Mark Earth Polygon')
    mars_p = poly(img, 'Mark Mars Polygon')
    post_p = poly(img, 'Mark Post Polygon')
    
    enull = ( (0,0), (0,0), 0)
    if not e1: e1 = enull
    if not e2: e2 = enull
    if not ee: ee = enull
    if not em: em = enull

    cimg = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    cimg2 = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    cv2.ellipse(cimg, e1, color=(0,255, 0, 1))
    cv2.ellipse(cimg, e2, color=(0,255, 0, 1))
    cv2.ellipse(cimg, ee, color=(0,255, 0, 1))
    cv2.ellipse(cimg, em, color=(0,255, 0, 1))
    
    if roi1: cv2.polylines(cimg2, [np.array(roi1).reshape(len(roi1), 1, 2)], isClosed=True, color=(255, 0, 0, 1))
    if earth_p: cv2.polylines(cimg2, [np.array(earth_p).reshape(len(earth_p), 1, 2)], isClosed=True, color=(255, 0, 0, 1))
    if mars_p:cv2.polylines(cimg2, [np.array(mars_p).reshape(len(mars_p), 1, 2)], isClosed=True, color=(255, 0, 0, 1))
    if post_p:cv2.polylines(cimg2, [np.array(post_p).reshape(len(post_p), 1, 2)], isClosed=True, color=(255, 0, 0, 1))
    
    
    cv2.namedWindow('result_e', flags=cv2.WINDOW_NORMAL)
    cv2.namedWindow('result_p', flags=cv2.WINDOW_NORMAL)
    cv2.imshow('result_e', cimg)
    cv2.imshow('result_p', cimg2)
    while True:
     key = cv2.waitKey()
     if key % 256 == ord('s'):
      try:
       data = (ident, json.dumps(e1), json.dumps(e2), json.dumps(ee), json.dumps(em), json.dumps(roi1), json.dumps(earth_p), json.dumps(mars_p), json.dumps(post_p))
       wcur.execute(wquery, data)
       wconn.commit()
      except Exception as e:
       print 'Could not add', ident
       print e
       wconn.rollback()
      else:
       print 'Addded', ident, fname
       break
     if key % 256 == 27: break
    
    cv2.destroyWindow('result_e')
    cv2.destroyWindow('result_p')
  
  if key % 256 == 27: break

def poly(img, wname):
 cv2.namedWindow(wname, flags=cv2.WINDOW_NORMAL)
 x, y = img.shape[1]/2, img.shape[0]/2
 points = list()
 key = -1
 while True:
  if key == 1113938: y = y - 1
  if key == 1376082: y = y - 5
  if key == 1113940: y = y + 1
  if key == 1376084: y = y + 5
  if key == 1113937: x = x - 1
  if key == 1376081: x = x - 5
  if key == 1113939: x = x + 1
  if key == 1376083: x = x + 5
  if key % 256 == 27:
   cv2.destroyWindow(wname)
   return list()
  if key == 1048586 and (x,y) not in points: points.append( (x,y) )
  if key == 1114111 and len(points) > 0: del points[-1]
  cimg = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
  cv2.line(cimg, (x,y), (x,y), (0, 0, 255, 1), lineType=4)
  for px,py in points: cv2.line(cimg, (px, py), (px,py), (255, 0, 0, 1))
  if key == 1048678:
   cv2.polylines(cimg, [np.array(points).reshape(len(points), 1, 2)], isClosed=True, color=(255, 0, 0, 1))
  if key == 1048676:
   cv2.destroyWindow(wname)
   return points
  
  cv2.imshow(wname, cimg)
  key = cv2.waitKey()
  
def ellipse(img, wname):
 cv2.namedWindow(wname, flags=cv2.WINDOW_NORMAL)
 x, y = img.shape[1]/2, img.shape[0]/2
 points = list() 
 
 key = -1
 while True:
  if key == 1113938: y = y - 1
  if key == 1376082: y = y - 5
  if key == 1113940: y = y + 1
  if key == 1376084: y = y + 5
  if key == 1113937: x = x - 1
  if key == 1376081: x = x - 5
  if key == 1113939: x = x + 1
  if key == 1376083: x = x + 5
  if key % 256 == 27:
   cv2.destroyWindow(wname)
   return None
  if key == 1048586 and (x,y) not in points: points.append( (x,y) )
  if key == 1114111 and len(points) > 0: del points[-1]
  cimg = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
  cv2.line(cimg, (x,y), (x,y), (0, 0, 255, 1), lineType=4)
  for px,py in points: cv2.circle(cimg, (px, py), 1, (255, 0, 0, 1))
  
  if key == 1048678 and len(points) > 4:
   efit = cv2.fitEllipse(np.array(points).reshape(len(points), 1, 2))
   cv2.ellipse(cimg, efit, (255, 0, 0, 1), lineType=4)
  if key == 1048676 and len(points) > 4:
   cv2.destroyWindow(wname)
   return cv2.fitEllipse(np.array(points).reshape(len(points), 1, 2))
  cv2.imshow(wname, cimg)
  key = cv2.waitKey()

def canny(img, t1=1, t2=1, aS=3):
 return cv2.Canny(img, t1, t2, apertureSize=aS, L2gradient=True)
 
def bilateralFilter(img, d=9, sc=100, ss=100):
 return cv2.bilateralFilter(img, d, sc, ss)

def scharr8bit(img):
 return cv2.convertScaleAbs(cv2.Scharr(img, ddepth=cv2.CV_32F, dx=1, dy=0))/2 + cv2.convertScaleAbs(cv2.Scharr(img, ddepth=cv2.CV_32F, dx=0, dy=1))/2
 

if __name__ == '__main__': Main()
