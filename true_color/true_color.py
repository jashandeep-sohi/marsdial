#!/usr/bin/python2

import numpy as np
import psycopg2 as ps
from psycopg2.extras import DictCursor
from psycopg2.extensions import AsIs
import argparse
import os
import bz2, cPickle
import json
import scipy.interpolate as interpolate
import cv2

def unpack_img(bzip2ed_pickled_img):
 return cPickle.loads(bz2.decompress(bzip2ed_pickled_img))

def scale_img(img, mi=0., ma=1.):
 return mi + (ma-mi) * ( (img-img.min()) / float(img.max()-img.min()) )

def cie_64_x(w):
 return 0.398 * np.exp(-1250. * np.log((w + 570.1)/1014.)**2 ) + 1.132 * np.exp(-234. * np.log((1338. - w)/743.5)**2)

def cie_64_y(w):
 return 1.011 * np.exp(-.5 * ((w - 556.1)/46.14)**2)

def cie_64_z(w):
 return 2.060 * np.exp(-32 * np.log((w - 265.8)/180.4)**2)

if __name__ == "__main__":
 arg_parser = argparse.ArgumentParser(
  description = "Generate true color images using filters L2, L3, L4, L5, L6 & L7."
 )
 arg_parser.add_argument(
  "output_dir",
  help = "Output directory."
 )
 arg_parser.add_argument(
  "--overwrite",
  help = "Use existing output directory, possibly overwriting files.",
  action = "store_true"
 )
 arg_parser.add_argument(
  "--host_id",
  help = "Rover ID.",
  choices = ["MER1", "MER2"],
  action = "append"
 )
 arg_parser.add_argument(
  "--limit",
  help = "Limit the number of results.",
  type = lambda s: AsIs("ALL") if int(s) < 0 else int(s),
  default = "-1"
 )
 arg_parser.add_argument(
  "--sol_start",
  help = "Start from this sol (helpful for resuming).",
  type = int,
  default = 0
 )
 arg_parser.add_argument(
  "--headers",
  help = "Generate headers.",
  action = "store_true"
 )
 arg_parser.add_argument(
  "--no_images",
  help = "Do not generate images.",
  action = "store_true"
 )
 cmd_args = arg_parser.parse_args()
 
 try:
  os.makedirs(cmd_args.output_dir)
 except OSError:
  if not cmd_args.overwrite:
   raise SystemExit("Error: Could not create new output directory.")
 
 conn = ps.connect("dbname=mars user=marsu", cursor_factory=DictCursor)
 
 imgs_cur = conn.cursor()
 
 ltst_group_cur = conn.cursor()
 ltst_group_cur.execute(
  r"""
   WITH
    q1 AS(
     SELECT
      pds_headers_v.*,
      extract(EPOCH FROM ltst) AS ltst_sec,
      left(filter_id, 1) AS filter_side,
      left(filter_wavelength, -2)::numeric AS filter_wavelength_nm
     FROM
      pds_headers_v
     WHERE
      host_id = ANY(%(host_id)s)
      AND filter_id != 'L1'
      AND sol >= %(sol_start)s
    ),
    q2 AS(
     SELECT
      q1.*,
      ltst_sec - lag(ltst_sec) OVER w AS ltst_diff,
      CASE 
       WHEN ltst_sec - lag(ltst_sec) OVER w > %(max_sec_diff)s THEN 1 ELSE 0
      END AS new_group_marker
     FROM
      q1
     WHERE
      filter_wavelength_nm BETWEEN 380 AND 780
     WINDOW w AS(
      PARTITION BY host_id, sol
      ORDER BY ltst
     )
    ),
    q3 AS(
     SELECT
      q2.*,
      sum(new_group_marker) OVER w AS ltst_group_id
     FROM
      q2
     WINDOW w AS(
      PARTITION BY host_id, sol
      ORDER BY ltst
     )
    ),
    q4 AS(
     SELECT DISTINCT ON(host_id, sol, ltst_group_id, filter_id)
      q3.*
     FROM
      q3
     ORDER BY
      host_id, sol, ltst_group_id, filter_id, ltst_sec
    )
   SELECT
    host_id,
    sol,
    filter_side,
    ltst_group_id,
    round(avg(ltst_sec))::integer as ltst_sec_avg,
    array_agg(id ORDER BY filter_wavelength_nm) as ids,
    array_agg(filter_id ORDER BY filter_wavelength_nm) as filter_ids
   FROM
    q4
   GROUP BY
    host_id, sol, ltst_group_id, filter_side, img_width, img_height
   HAVING
    count(*) = 6
   ORDER BY
    host_id, sol, ltst_group_id, filter_side, img_width, img_height
   LIMIT %(limit)s
  """,
  {
   "max_sec_diff": 300,
   "host_id": cmd_args.host_id,
   "limit": cmd_args.limit,
   "sol_start": cmd_args.sol_start
  }
 ) 
 
 wavelength_fine = np.arange(380, 780+1, 1)
 cm_xyz = [f(wavelength_fine) for f in (cie_64_x, cie_64_y, cie_64_z)]
 
 
 for row in ltst_group_cur:
  print "Processing:", row["host_id"], row["sol"], row["ltst_group_id"], row["ltst_sec_avg"], row["filter_side"]
  print "Filters:", row["filter_ids"]
  
  # Base file name
  file_name = "{host}.{sol}.{ltst_group}.{filter_side}.{filter_ids}".format(
    host = row["host_id"],
    sol = row["sol"],
    ltst_group = row["ltst_group_id"],
    filter_side = row["filter_side"],
    filter_ids = '-'.join(row["filter_ids"])
   )
  
  # Fetch image & headers.
  imgs_cur.execute(
   r"""
    SELECT
     image_py,
     headers_json,
     filter_id,
     left(filter_wavelength, -2)::integer AS filter_wavelength_nm
    FROM
     pds_files JOIN pds_headers_v USING(id)
    WHERE
     id = ANY(%(ids)s)
    ORDER BY
     filter_wavelength_nm
   """,
   {"ids": row["ids"]}
  )
  imgs_res = imgs_cur.fetchall()
  
  if not cmd_args.no_images:
   wavelengths = np.hstack(x["filter_wavelength_nm"] for x in imgs_res)
   imgs = np.dstack(unpack_img(x["image_py"]) for x in imgs_res)
   
   print "Interpolating..."
   #Spline interpolate of order 3
   spline = interpolate.interp1d(
    wavelengths,
    imgs,
    3,
    2,
    False,
    False,
    0
   )
     
   print "Generating XYZ interpolated colourspace image..."
   interp_values = spline(wavelength_fine)
   out_img_xyz = np.empty((imgs.shape[0], imgs.shape[1], 3))
   for i in xrange(0,3):
    out_img_xyz[...,i] = np.sum(interp_values * cm_xyz[i], 2)
   
   print "Transforming XYZ colourspace to BGR colourspace..."
   # Transform to BGR **linear** values
   out_img_bgr = out_img_xyz.dot(
     [[0.0557, -0.9689, 3.2406],
      [-0.204, 1.8758, -1.5372],
      [1.0570, 0.0415, -0.4986]] 
   )
   
   # Normalize 0 to 1
   out_img_bgr = (out_img_bgr - out_img_bgr.min()) / (out_img_bgr.max() - out_img_bgr.min())
   
   # Finally sBGR transformation.
   cond = out_img_bgr <= 0.0031308
   out_img_bgr[cond] = 12.92 * out_img_bgr[cond]
   out_img_bgr[~cond] = ((1 + 0.055) * out_img_bgr[~cond]**(1/2.4)) - 0.055
   
   out_img_bgr = np.rint(255 * out_img_bgr).astype("uint8")
    
   # Save image
   img_file_name = "{}.png".format(file_name)
   print "Saving image to {}".format(img_file_name)
   cv2.imwrite(
    "{}/{}".format(cmd_args.output_dir, img_file_name),
    out_img_bgr,
    [cv2.IMWRITE_PNG_COMPRESSION, 9]
   )
  
  # Save headers
  if cmd_args.headers:
   headers_file_name = "{}.headers.json".format(file_name)
   print "Saving headers to {}".format(headers_file_name)
   with open("{}/{}".format(cmd_args.output_dir, headers_file_name), "w") as jf:
    json.dump(
     {
      "host": row["host_id"],
      "sol": row["sol"],
      "ltst_group_id": row["ltst_group_id"],
      "filter_side": row["filter_side"],
      "filters": row["filter_ids"],
      "ltst_sec_avg": row["ltst_sec_avg"],
      "headers": { x["filter_id"]: x["headers_json"] for x in imgs_res }
     },
     jf
    )
    
 print "Total results:", ltst_group_cur.rowcount
