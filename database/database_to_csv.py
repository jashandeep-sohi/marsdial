#!/usr/bin/python2

import psycopg2 as ps
from psycopg2.extras import DictCursor

if __name__ == '__main__':
 conn = ps.connect("dbname=mars user=marsu", cursor_factory=DictCursor)
 cur = conn.cursor()
 
 copy_query = r"""
 COPY (
  SELECT DISTINCT ON(pds_headers_v.id)
   pds_headers_v.*,
   phot_vals_disk1.shadow_mean,
   phot_vals_disk1.shadow_mean * pds_headers_v.radiance_scaling_factor +
    pds_headers_v.radiance_offset as shadow_mean_corrected,
   phot_vals_disk1.light_mean,
   phot_vals_disk1.light_mean * pds_headers_v.radiance_scaling_factor +
    pds_headers_v.radiance_offset as light_mean_corrected,
   phot_vals_disk1.shadow_std,
   phot_vals_disk1.light_std,
   phot_vals_disk1.shadow_pixels,
   phot_vals_disk1.light_pixels,
   atmos_opacities_v.filter_name as atmos_opacity_filter_name,
   atmos_opacities_v.ltst as atmos_opacity_ltst,
   atmos_opacities_v.solar_longitude as atmos_opacity_solar_longitude,
   atmos_opacities_v.solar_distance as atmos_opacity_solar_distance,
   atmos_opacities_v.airmass as atmos_opacity_airmass,
   atmos_opacities_v.solar_flux as atmos_opacity_solar_flux,
   atmos_opacities_v.atmos_opacity,
   atmos_opacities_v.atmos_opacity_err,
   atmos_opacities_v.filter_id as atmos_opacity_filter_id,
   atmos_opacities_v.filter_wavelength as atmos_opacity_wavelength
  FROM
   pds_headers_v
   JOIN phot_vals_disk1 USING(id)
   JOIN atmos_opacities_v USING(sol, host_id)
  WHERE
   atmos_opacities_v.filter_id = 'R8'
  ORDER BY
   pds_headers_v.id,
   abs(extract(EPOCH FROM pds_headers_v.ltst - atmos_opacities_v.ltst))
 ) TO STDOUT WITH FORMAT csv HEADER;
 """
 with open("dataset.csv", "w") as csv_file:
  cur.copy_expert(copy_query, csv_file)
