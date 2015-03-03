#!/usr/bin/env python2

import psycopg2 as ps
import datetime
import numpy as np

#http://www.giss.nasa.gov/tools/mars24/help/algorithm.html
#ftp://maia.usno.navy.mil/ser7/tai-utc.dat

def getLeapSeconds(time_utc):
 tai_minus_utc = (
  (datetime.datetime(2012, 07, 01), 35.0),
  (datetime.datetime(2009, 01, 01), 34.0),
  (datetime.datetime(2006, 01, 01), 33.0),
  (datetime.datetime(1999, 01, 01), 32.0),
 )
 for d, dt in tai_minus_utc:
  if time_utc >= d:
   return datetime.timedelta(seconds=dt)
 return None
  

def calcLMST(ltst, solar_longitude, time_utc):
 j2000 = datetime.datetime(2000, 01, 01, 12, 00, 00)
 leap_sec = getLeapSeconds(time_utc)
 delta_j2000 = (time_utc + leap_sec + datetime.timedelta(seconds=33)) - j2000
 delta_j2000_d = delta_j2000.total_seconds()/86400.

 fiction_mean_sun_angle = (270.3863 + 0.52403840 * delta_j2000_d) % 360

 solar_longitude = solar_longitude % 360
 L_s = np.radians(solar_longitude)
 eot_deg = 2.861 * np.sin(2 * L_s) - 0.071 * np.sin(4 * L_s) + 0.002 * np.sin(6 * L_s) - (solar_longitude - fiction_mean_sun_angle)
 
 ltst_elms = map(float, ltst.split(':'))
 ltst_deg = (15*ltst_elms[0]) + (ltst_elms[1]/4.) + (ltst_elms[2]/240.)
 
 lmst_deg = ltst_deg - eot_deg

 return datetime.timedelta(hours=lmst_deg * 24/360.)
 
 

def makePDSHeadersTable(conn):
 wcur = conn.cursor()
 rcur = conn.cursor('json_headers')
 rq = """SELECT id, headers_json FROM pds_files;"""
 wq = """
 INSERT INTO pds_headers (
  id,
  sol,
  img_width,
  img_height,
  host_id,
  filter_name,
  ltst,
  lmst,
  solar_longitude,
  rfd_inst_azimuth,
  rfd_inst_elevation,
  sfd_inst_azimuth,
  sfd_inst_elevation,
  sfd_solar_azimuth,
  sfd_solar_elevation,
  radiance_offset,
  radiance_scaling_factor,
  rcs_rotation_quaternion
 )
 VALUES (
  %(id)s,
  %(sol)s,
  %(img_width)s,
  %(img_height)s,
  %(host_id)s,
  %(filter_name)s,
  %(ltst)s,
  %(lmst)s,
  %(solar_longitude)s,
  %(rfd_inst_azimuth)s,
  %(rfd_inst_elevation)s,
  %(sfd_inst_azimuth)s,
  %(sfd_inst_elevation)s,
  %(sfd_solar_azimuth)s,
  %(sfd_solar_elevation)s,
  %(radiance_offset)s, 
  %(radiance_scaling_factor)s,
  %(rcs_rotation_quaternion)s ::numeric[]
 );"""
 rcur.execute(rq)
 wcur.execute('TRUNCATE pds_headers;')
 for i,row in enumerate(rcur):
  p_id = row[0]
  print i,p_id
  h = row[1]
  values = {
   'id': p_id,
   'sol': h['planet_day_number'],
   'img_width': h['image']['line_samples'],
   'img_height': h['image']['lines'],
   'host_id': h['instrument_host_id'],
   'filter_name': h['instrument_state_parms']['filter_name'],
   'ltst': h['local_true_solar_time'],
   'solar_longitude': float(h['solar_longitude']) % 360,
   'rfd_inst_azimuth': float(h['rover_derived_geometry_parms']['instrument_azimuth'].strip(' <deg>')) % 360,
   'rfd_inst_elevation': float(h['rover_derived_geometry_parms']['instrument_elevation'].strip(' <deg>')) % 360,
   'sfd_inst_azimuth': float(h['site_derived_geometry_parms']['instrument_azimuth'].strip(' <deg>')) % 360,
   'sfd_inst_elevation': float(h['site_derived_geometry_parms']['instrument_elevation'].strip(' <deg>')) % 360,
   'sfd_solar_azimuth': float(h['site_derived_geometry_parms']['solar_azimuth'].strip(' <deg>')) % 360,
   'sfd_solar_elevation': float(h['site_derived_geometry_parms']['solar_elevation'].strip(' <deg>')) % 360,
   'radiance_offset': h['derived_image_parms']['radiance_offset'],
   'radiance_scaling_factor': h['derived_image_parms']['radiance_scaling_factor'],
   'rcs_rotation_quaternion': h['rover_coordinate_system']['origin_rotation_quaternion'].strip('"()').split(','),
  }
  time_fmt = '%Y-%m-%dT%H:%M:%S.%fZ'
  start_time = datetime.datetime.strptime(h['start_time'], time_fmt)
  stop_time = datetime.datetime.strptime(h['stop_time'], time_fmt)
  utc_time_avg = start_time + (stop_time - start_time)/2 
  values['lmst'] = calcLMST(values['ltst'], values['solar_longitude'], utc_time_avg)
  wcur.execute(wq, values)
 conn.commit()

if __name__ == '__main__':
 conn = ps.connect(user='mars', database='mars')
 makePDSHeadersTable(conn)
