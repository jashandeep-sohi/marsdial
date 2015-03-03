#!/usr/bin/env python2

import urllib2
import psycopg2 as ps

def makeAtmosOpacitiesTable(conn):
 table_urls = (
  'http://gemelli.colorado.edu/~wolff/MER/pancam/tau/00_A_TAU_440.TAB',
  'http://gemelli.colorado.edu/~wolff/MER/pancam/tau/00_A_TAU_880.TAB',
  'http://gemelli.colorado.edu/~wolff/MER/pancam/tau/00_B_TAU_440.TAB',
  'http://gemelli.colorado.edu/~wolff/MER/pancam/tau/00_B_TAU_880.TAB',
 )
 wcur = conn.cursor()
 wq = """
 INSERT INTO atmos_opacities (
  id,
  sol,
  host_id,
  filter_name,
  ltst,
  solar_longitude,
  solar_distance,
  airmass,
  solar_flux,
  atmos_opacity,
  atmos_opacity_err
 )
 VALUES (
  %(id)s,
  %(sol)s,
  %(host_id)s,
  %(filter_name)s,
  %(ltst)s,
  %(solar_longitude)s,
  %(solar_distance)s,
  %(airmass)s,
  %(solar_flux)s,
  %(atmos_opacity)s,
  %(atmos_opacity_err)s
 );""";
 wcur.execute('TRUNCATE atmos_opacities;')
 for table_url in table_urls:
  table_content = urllib2.urlopen(table_url)
  for _ in xrange(9):
   next(table_content)
  for line in table_content:
   elms = line.strip().split(',')
   vals = map(float, elms[1:])
   
   p_id = elms[0].strip('"')
   
   lt_i, lt_d = divmod(vals[2], 1)
   
   hours, mins_d = divmod(lt_d*24, 1)
   mins, secs_d = divmod(mins_d*60, 1) 
   
   filter_id = p_id[23:25]
   filter_name_d = {'R8': '880NM', 'L8': '440NM' }
   
   values = {
    'id': p_id,
    'sol': int(lt_i) + 1,
    'host_id': 'MER{}'.format(p_id[0]),
    'filter_name': 'PANCAM_{}_{}'.format( filter_id, filter_name_d[filter_id] ),
    'ltst': '{:.0f}:{:.0f}:{}'.format(hours, mins, secs_d*60),
    'solar_longitude': vals[0] % 360,
    'solar_distance': vals[1],
    'airmass': vals[3],
    'solar_flux': vals[4],
    'atmos_opacity': vals[5],
    'atmos_opacity_err': vals[6],
   }
   print p_id
   try:
    wcur.execute(wq, values)
   except ps.IntegrityError as e:
    print e
    conn.rollback()
   else:
    conn.commit()
    
if __name__ == '__main__':
 conn = ps.connect(user='mars', database='mars')
 makeAtmosOpacitiesTable(conn)
