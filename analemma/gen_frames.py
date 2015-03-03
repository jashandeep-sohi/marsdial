#!/usr/bin/python2

import argparse
import os
import psycopg2 as ps
from psycopg2.extensions import AsIs
from psycopg2.extras import Json, DictCursor
import bz2, cPickle
import numpy as np
import cv2
import colorsys
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

def unpack_img(bzip2ed_pickled_img):
 return cPickle.loads(bz2.decompress(bzip2ed_pickled_img))
 
def normalize_img(img, mi=0., ma=1.):
 return mi + (ma-mi) * ( (img-img.min()) / float(img.max()-img.min()) )
 
def scharr_img(img):
 return cv2.convertScaleAbs(cv2.Scharr(img, ddepth=cv2.CV_32F, dx=1, dy=0)) / 2 + \
  cv2.convertScaleAbs(cv2.Scharr(img, ddepth=cv2.CV_32F, dx=0, dy=1)) / 2
  
def on_mouse_mark_shadow(
 event,
 x,
 y,
 flags,
 (elps_pts, img_color, img_scharr_color, shadow_elps_ref)
):
 if event == cv2.EVENT_LBUTTONUP:
  elps_pts.append([x,y])
  print "Added point", [x,y], "to ellipse fit."
 
 if event == cv2.EVENT_RBUTTONUP:
  try:
   print "Removed point", elps_pts.pop(), "from ellipse fit."
  except IndexError:
   pass
 
 if event == cv2.EVENT_LBUTTONUP or event == cv2.EVENT_RBUTTONUP:
  img_color_temp = img_color.copy()
  img_scharr_color_temp = img_scharr_color.copy()
  
  for x,y in elps_pts:
   cv2.circle(img_color_temp, (x,y), 1, (0, 0, 255), lineType=4)
   cv2.circle(img_scharr_color_temp, (x,y), 1, (0, 0 , 255), lineType=4)
  
  if len(elps_pts) > 4:
   shadow_elps_ref[0] = cv2.fitEllipse(np.array(elps_pts))
   cv2.ellipse(img_color_temp, shadow_elps_ref[0], (255, 0, 0))
   cv2.ellipse(img_scharr_color_temp, shadow_elps_ref[0], (255, 0, 0))
  
  cv2.imshow("mark image", img_color_temp)
  cv2.imshow("mark image (scharr)", img_scharr_color_temp)

def mark_shadow_ellipse(img_gray):
 img_color = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)
 img_scharr_color = cv2.cvtColor(
  scharr_img(img_gray),
  cv2.COLOR_GRAY2BGR
 )
 elps_pts = list()
 shadow_elps_ref = [None]
 cv2.namedWindow("mark image", cv2.WINDOW_NORMAL)
 cv2.namedWindow("mark image (scharr)", cv2.WINDOW_NORMAL)
 cv2.setMouseCallback(
  "mark image",
  on_mouse_mark_shadow,
  (elps_pts, img_color, img_scharr_color, shadow_elps_ref)
 )
 cv2.setMouseCallback("mark image (scharr)",
  on_mouse_mark_shadow,
  (elps_pts, img_color, img_scharr_color, shadow_elps_ref)
 )
 cv2.imshow("mark image", img_color)
 cv2.imshow("mark image (scharr)", img_scharr_color)
 while True:
  if cv2.waitKey(100) % 256 == 27:
   break
 return shadow_elps_ref[0]

def calc_rrect_cross_pts(center, width, height, rot_rads):
 p1 = center + width/2. * np.array([np.cos(rot_rads), np.sin(rot_rads)])
 p2 = center + height/2. * np.array([np.cos(rot_rads + np.pi/2.), np.sin(rot_rads + np.pi/2.)])
 p3 = center + width/2. * np.array([np.cos(rot_rads + np.pi), np.sin(rot_rads + np.pi)])
 p4 = center + height/2. * np.array([np.cos(rot_rads + 1.5*np.pi), np.sin(rot_rads + 1.5*np.pi)])
 return np.array([p1, p2, p3, p4])

if __name__ == "__main__":
 arg_parser = argparse.ArgumentParser(
  description = "Manipulates MarsDial images into analemma animation frames.",
  formatter_class = argparse.ArgumentDefaultsHelpFormatter
 )
 arg_parser.add_argument(
  "host_id",
  help = "Rover ID. {%(choices)s}",
  metavar = "host_id",
  choices = ["MER1", "MER2"]
 )
 arg_parser.add_argument(
  "output_dir",
  help = "Directory in which to save output frames."
 )
 arg_parser.add_argument(
  "--order_by",
  help = "Order images by.",
  choices = ["sol", "solar_longitude", "random", "random()"],
  type = lambda s: "random()" if s == "random" else s,
  default = "sol"
 )
 arg_parser.add_argument(
  "--limit",
  help = "Maximum number of images to process.",
  type = lambda s: AsIs("ALL") if int(s) < 0 else int(s),
  default = "-1"
 )
 arg_parser.add_argument(
  "--roll_max",
  help = "Maximum roll of the rover in degrees.",
  type = int,
  default = 10
 )
 arg_parser.add_argument(
  "--roll_min",
  help = "Minimum roll of the rover in degrees.",
  type = int,
  default = -10
 )
 arg_parser.add_argument(
  "--pitch_max",
  help = "Maximum pitch of the rover in degrees.",
  type = int,
  default = 10
 )
 arg_parser.add_argument(
  "--pitch_min",
  help = "Minimum pitch of the rover in degrees.",
  type = int,
  default = -10
 )
 arg_parser.add_argument(
  "--transition_frames",
  help = "Number of transition frames between each animation frame.",
  type = int,
  default = 5
 )
 arg_parser.add_argument(
  "--preview_pause",
  help = "Number of milliseconds to wait between frames on preview window.",
  type = int,
  default = 1
 )
 arg_parser.add_argument(
  "--no_save",
  help = "Do not write any thing to disk.",
  action = "store_true"
 )
 arg_parser.add_argument(
  "--no_save_animation",
  help = "Do not save the generated analemma animation frames.",
  action = "store_true"
 )
 arg_parser.add_argument(
  "--procedure",
  help = "Generate procedural images.",
  action = "store_true"
 )
 arg_parser.add_argument(
  "--save_procedure",
  help = "Save procedureal images.",
  action = "store_true"
 )
 arg_parser.add_argument(
  "--save_centers",
  help = "Save expected & measured centers in data file.",
  action = "store_true"
 )
 arg_parser.add_argument(
  "--plots",
  help = "Make & save plots.",
  action = "store_true"
 )
 cmd_args = arg_parser.parse_args()
 
 if not cmd_args.no_save:
  try:
   os.makedirs(cmd_args.output_dir)
  except OSError:
   pass
  if cmd_args.save_centers:
   measured_centers_data_file = open(
    "{:}/measured_analemma_centers.data".format(cmd_args.output_dir),
    "w"
   )
   measured_centers_data_file.write(
    "# sol, solar_longitude (deg), shadow_center_x (mm), shadow_center_y (mm)\n"
   )
 
 readable_connection = ps.connect(
  "dbname=mars user=marsu",
  cursor_factory=DictCursor
 )
 writable_connection = ps.connect(
  "dbname=mars user=mars",
  cursor_factory=DictCursor
 )
 
 writable_cursor = writable_connection.cursor()
 images_cursor = readable_connection.cursor()
 
 images_query = r"""
  WITH temp_table AS (
   SELECT DISTINCT ON(pds_headers_v.sol)
    pds_files.id,
    pds_files.image_py,
    pds_headers_v.sol,
    pds_headers_v.solar_longitude::double precision,
    pds_headers_v.sfd_solar_azimuth::double precision as solar_azimuth,
    pds_headers_v.sfd_solar_elevation::double precision as solar_elevation,
    image_regs.dx::double precision as shift_dx,
    image_regs.dy::double precision as shift_dy,
    ref_images.elps_middle as middle_ellipse_rrect,
    shadow_pos.elps_rrect as shadow_ellipse_rrect
   FROM
    pds_files
    JOIN pds_headers_v USING(id)
    JOIN image_regs USING(id)
    LEFT JOIN shadow_pos USING(id)
    JOIN ref_images ON(image_regs.ref_id = ref_images.id)
   WHERE
    pds_headers_v.lmst BETWEEN
     %(target_lmst)s::interval - %(target_lmst_err)s AND
     %(target_lmst)s::interval + %(target_lmst_err)s
    AND pds_headers_v.host_id = %(host_id)s
    AND pds_headers_v.filter_id = ANY(%(filter_ids)s)
    AND round(degrees(calc_roll(pds_headers_v.rcs_rotation_quaternion)))
     BETWEEN %(roll_min)s AND %(roll_max)s
    AND round(degrees(calc_pitch(pds_headers_v.rcs_rotation_quaternion)))
     BETWEEN %(pitch_min)s AND %(pitch_max)s
   ORDER BY
    pds_headers_v.sol,
    abs(extract(EPOCH FROM pds_headers_v.lmst - %(target_lmst)s))
  )
  SELECT temp_table.* FROM temp_table ORDER BY %(order_by)s LIMIT %(limit)s;
 """
 images_query_opts = {
  "host_id": cmd_args.host_id,
  "limit": cmd_args.limit,
  "roll_min": cmd_args.roll_min,
  "roll_max": cmd_args.roll_max,
  "pitch_min": cmd_args.pitch_min,
  "pitch_max": cmd_args.pitch_max,
  "order_by": AsIs(cmd_args.order_by),
  "filter_ids": [
   "R1", "R2", "R3", "R4", "R5", "R6", "R7",
   "L1", "L2", "L3", "L4", "L5", "L6", "L7"
   ],
  "target_lmst_err": "00:05:00",
  "target_lmst": "12:01:10" if cmd_args.host_id == "MER1" else "11:51:19"
 }
  
 images_cursor.execute(images_query, images_query_opts)
 
 print "Total images:", images_cursor.rowcount
 
 procedure_index = 0
 frame_index = 0
 prev_out_img_bgr = None
 sh_centers = list()
 for row in images_cursor:
  print "Processing:", row["id"]
  
  img_uint8 = np.rint(
   normalize_img(unpack_img(row["image_py"]), 0, 255)
  ).astype("uint8")
  img_bgr = cv2.cvtColor(img_uint8, cv2.COLOR_GRAY2BGR)
   
  if row["shadow_ellipse_rrect"] == None:
   print "Shadow ellipse has not been marked for this image, yet. Mark the shadow..."
   shadow_ellipse_rrect = mark_shadow_ellipse(img_uint8)
   if shadow_ellipse_rrect:
    writable_cursor.execute(
     "INSERT INTO shadow_pos (id, elps_rrect) VALUES (%s, %s);",
     (row['id'], Json(shadow_ellipse_rrect))
    )
    writable_cursor.connection.commit()
    print "Recoreded shadow position of", row["id"]
   else:
    print "Skipping: shadow not marked."
    continue
  else:
   shadow_ellipse_rrect = row["shadow_ellipse_rrect"]
  
  shadow_ellipse_center = np.array(shadow_ellipse_rrect[0])
  shadow_ellipse_points = cv2.ellipse2Poly(
   tuple(np.rint(shadow_ellipse_center).astype("int")),
   tuple(np.rint(np.array(shadow_ellipse_rrect[1]) / 2.).astype("int")),
   np.rint(shadow_ellipse_rrect[2]).astype("int"),
   0,
   360,
   1
  )
  
  middle_ellipse_center = np.array(row["middle_ellipse_rrect"][0]) + \
   [row["shift_dx"], row["shift_dy"] ]
  middle_ellipse_width, middle_ellipse_height = row["middle_ellipse_rrect"][1]
  middle_ellipse_rot_rad = np.radians(row["middle_ellipse_rrect"][2])
  middle_ellipse_cross_points = calc_rrect_cross_pts(
   middle_ellipse_center,
   middle_ellipse_width,
   middle_ellipse_height,
   middle_ellipse_rot_rad
  )
  
  proj_middle_ellipse_center = np.array([320, 272])/2
  proj_middle_ellipse_cross_points = calc_rrect_cross_pts(
   proj_middle_ellipse_center,
   middle_ellipse_height,
   middle_ellipse_height,
   middle_ellipse_rot_rad
  )
  proj_perspective_matrix = cv2.getPerspectiveTransform(
   middle_ellipse_cross_points.reshape(4,1,2).astype('float32'),
   proj_middle_ellipse_cross_points.reshape(4,1,2).astype('float32')
  )
  proj_shadow_ellipse_center = cv2.perspectiveTransform(
   shadow_ellipse_center.reshape(1,1,2), proj_perspective_matrix
  ).reshape(2)
  proj_shadow_ellipse_points = cv2.perspectiveTransform(
   shadow_ellipse_points.astype('float32').reshape(shadow_ellipse_points.shape[0],1,2),
   proj_perspective_matrix).reshape(shadow_ellipse_points.shape[0], 2)
  
  proj_shadow_angle_rad = np.arctan2(
   *(proj_shadow_ellipse_center - proj_middle_ellipse_center)[::-1]
  ) + np.pi
  proj_north_angle_rad = proj_shadow_angle_rad - np.radians(row["solar_azimuth"])
  
  rot_middle_ellipse_center = proj_middle_ellipse_center
  rot_middle_ellipse_cross_points = calc_rrect_cross_pts(
   rot_middle_ellipse_center,
   middle_ellipse_height,
   middle_ellipse_height,
   middle_ellipse_rot_rad - proj_north_angle_rad
  )
  rot_perspective_matrix = cv2.getPerspectiveTransform(
   middle_ellipse_cross_points.reshape(4,1,2).astype('float32'),
   rot_middle_ellipse_cross_points.reshape(4,1,2).astype('float32')
  )
  rot_shadow_ellipse_center = cv2.perspectiveTransform(
   shadow_ellipse_center.reshape(1,1,2), rot_perspective_matrix
  ).reshape(2)
  rot_shadow_ellipse_points = cv2.perspectiveTransform(
   shadow_ellipse_points.astype('float32').reshape(shadow_ellipse_points.shape[0],1,2),
   rot_perspective_matrix).reshape(shadow_ellipse_points.shape[0], 2)
  
  sh_color = np.rint(
   colorsys.hsv_to_rgb(row["solar_longitude"]/360., 1, 1) * np.array([255, 255, 255])
  ).astype('int')[::-1]
  sh_centers.append( (sh_color, rot_shadow_ellipse_center) )
    
  if not cmd_args.no_save and cmd_args.save_centers:
   pixels_to_mm = 55./middle_ellipse_height
   shadow_ellipse_center_from_center = pixels_to_mm * (rot_shadow_ellipse_center - rot_middle_ellipse_center)
   measured_centers_data_file.write(
    "{:} {:} {:} {:}\n".format(
    row["sol"],
    row["solar_longitude"],
    shadow_ellipse_center_from_center[0],
    -shadow_ellipse_center_from_center[1],
    )
   )
  
  # Output section  
  rot_img_bgr = cv2.warpPerspective(img_bgr, rot_perspective_matrix, (320, 272))
  out_img_bgr = cv2.resize(
   rot_img_bgr,
   (0,0),
   fx = 2,
   fy = 2,
   interpolation = cv2.INTER_CUBIC
  )
  
  cv2.putText(
   out_img_bgr,
    "Opportunity" if cmd_args.host_id == "MER1" else "Spirit",
   (10, 30),
   cv2.FONT_HERSHEY_COMPLEX,
   1,
   (255, 255, 255),
   2,
   cv2.CV_AA
  )
  cv2.putText(
   out_img_bgr,
   "Ls={:05.1f} deg".format(row["solar_longitude"]),
   (out_img_bgr.shape[1] - 235, out_img_bgr.shape[0] - 15),
   cv2.FONT_HERSHEY_COMPLEX,
   1,
   sh_color,
   2,
   cv2.CV_AA
  )
  cv2.putText(
   out_img_bgr,
   "Sol:{:4d}".format(row["sol"]),
   (out_img_bgr.shape[1] - 150, 30),
   cv2.FONT_HERSHEY_COMPLEX,
   1,
   (255, 255, 255),
   2,
   cv2.CV_AA
  )
  cv2.putText(
   out_img_bgr,
   "N",
   (20, out_img_bgr.shape[0] - 20),
   cv2.FONT_HERSHEY_COMPLEX,
   1,
   (0, 0, 255),
   2,
   cv2.CV_AA
  )
  cv2.circle(
   out_img_bgr,
   (30, out_img_bgr.shape[0] - 30),
   19,
   (255, 255, 255),
   1,
   cv2.CV_AA
  )
  cv2.fillConvexPoly(
   out_img_bgr,
   np.array([55, out_img_bgr.shape[0] - 30]) + np.array([
    [0, 0],
    [-5, 10],
    [20, 0],
    [-5, -10]
   ]),
   (0, 0, 255),
   cv2.CV_AA
  )   
  cv2.ellipse(
   out_img_bgr,
   cv2.fitEllipse(2 * rot_shadow_ellipse_points),
   sh_color,
   2,
   cv2.CV_AA
  )
  for color, center in sh_centers:
   cv2.circle(
    out_img_bgr,
    tuple(2 * np.rint(center).astype("int")),
    3,
    color,
    -1,
    cv2.CV_AA
   )
  cv2.fillPoly(
   out_img_bgr,
   [ 2*rot_middle_ellipse_center + np.array([
    [-2, 0],
    [-7, 7],
    [0, 2],
    [7, 7],
    [2, 0],
    [7, -7],
    [0, -2],
    [-7, -7]
   ])],
   (0, 255, 255),
   cv2.CV_AA
  )
    
  cv2.namedWindow("animation preview", cv2.WINDOW_NORMAL)
  
  if prev_out_img_bgr != None:
   for i in np.linspace(
    1./(cmd_args.transition_frames+1),
    1-1./(cmd_args.transition_frames+1),
    cmd_args.transition_frames
   ):
    transition_img_bgr = np.rint(
     i * out_img_bgr + (1. - i) * prev_out_img_bgr
    ).astype('uint8')
    if not cmd_args.no_save and not cmd_args.no_save_animation:
     cv2.imwrite(
      "{path}/animation.{fi}.png".format(
       path = cmd_args.output_dir,
       fi = frame_index
      ),
      transition_img_bgr
     )
     frame_index += 1
    cv2.imshow("animation preview", transition_img_bgr)
    cv2.waitKey(cmd_args.preview_pause)
  
  if not cmd_args.no_save and not cmd_args.no_save_animation:
   cv2.imwrite(
    "{path}/animation.{fi}.png".format(
     path = cmd_args.output_dir,
     fi = frame_index
    ),
    out_img_bgr
   )
   frame_index += 1
  cv2.imshow("animation preview", out_img_bgr)
  prev_out_img_bgr = out_img_bgr
  
  # Procedure section
  if cmd_args.procedure:
   cv2.namedWindow("procedure preview", cv2.WINDOW_NORMAL)
   
   # Marked image
   procedure_marked_img_bgr = img_bgr.copy()
   cv2.ellipse(
    procedure_marked_img_bgr,
    (
     middle_ellipse_center,
     (middle_ellipse_width, middle_ellipse_height),
     np.degrees(middle_ellipse_rot_rad)
    ),
    (0, 0, 255),
    1,
    cv2.CV_AA
   )
   cv2.ellipse(
    procedure_marked_img_bgr,
    tuple(shadow_ellipse_rrect),
    (255, 0, 0),
    1,
    cv2.CV_AA
   )
   cv2.circle(
    procedure_marked_img_bgr,
    tuple(np.rint(shadow_ellipse_center).astype("int")),
    1,
    (255, 0, 0),
    -1,
    cv2.CV_AA
   )
   cv2.circle(
    procedure_marked_img_bgr,
    tuple(np.rint(middle_ellipse_center).astype("int")),
    1,
    (0, 0, 255),
    -1,
    cv2.CV_AA
   )
   for cross_pt, color in zip(
    middle_ellipse_cross_points,
    [(255, 255, 0), (0, 255, 255), (255, 0, 255), (0, 255,0)]
   ):
    cv2.circle(
     procedure_marked_img_bgr,
     tuple(np.rint(cross_pt).astype("int")),
     3,
     color,
     -1,
     cv2.CV_AA
    )
   
   # Projected image
   procedure_proj_img_bgr = cv2.warpPerspective(
    img_bgr,
    proj_perspective_matrix,
    (320, 272)
   )
   cv2.line(
    procedure_proj_img_bgr,
    tuple(np.rint(proj_middle_ellipse_center).astype("int")),
    tuple(np.rint(proj_shadow_ellipse_center).astype("int")),
    (255, 0, 0),
    1,
    cv2.CV_AA
   )
   cv2.fillConvexPoly(
    procedure_proj_img_bgr,
    np.rint(np.array([
    proj_middle_ellipse_center,
    proj_middle_ellipse_center + middle_ellipse_height/2. * np.array([
     np.cos(proj_north_angle_rad+np.radians(3)),
     np.sin(proj_north_angle_rad+np.radians(3))
    ]),
    proj_middle_ellipse_center + (15+middle_ellipse_height/2.) * np.array([
     np.cos(proj_north_angle_rad),
     np.sin(proj_north_angle_rad)
    ]),
    proj_middle_ellipse_center + middle_ellipse_height/2. * np.array([
     np.cos(proj_north_angle_rad-np.radians(3)),
     np.sin(proj_north_angle_rad-np.radians(3))
    ])
    ])).astype("int"),
    (0, 0, 255),
    cv2.CV_AA
   )
   cv2.putText(
    procedure_proj_img_bgr,
    "N",
    tuple(np.rint(
     proj_middle_ellipse_center + (30+middle_ellipse_height/2.) * np.array([
      np.cos(proj_north_angle_rad),
      np.sin(proj_north_angle_rad)
     ])
    ).astype("int")),
    cv2.FONT_HERSHEY_PLAIN,
    1,
    (0, 0, 255),
    1,
    cv2.CV_AA
   )
   cv2.ellipse(
    procedure_proj_img_bgr,
    (
     proj_middle_ellipse_center,
     (middle_ellipse_height, middle_ellipse_height),
     np.degrees(middle_ellipse_rot_rad)
    ),
    (0, 0, 255),
    1,
    cv2.CV_AA
   )
   cv2.ellipse(
    procedure_proj_img_bgr,
    cv2.fitEllipse(proj_shadow_ellipse_points),
    (255, 0, 0),
    1,
    cv2.CV_AA
   )
   cv2.circle(
    procedure_proj_img_bgr,
    tuple(np.rint(proj_shadow_ellipse_center).astype("int")),
    1,
    (255, 0, 0),
    -1,
    cv2.CV_AA
   )
   cv2.circle(
    procedure_proj_img_bgr,
    tuple(np.rint(proj_middle_ellipse_center).astype("int")),
    1,
    (0, 0, 255),
    -1,
    cv2.CV_AA
   )
   for cross_pt, color in zip(
    proj_middle_ellipse_cross_points,
    [(255, 255, 0), (0, 255, 255), (255, 0, 255), (0, 255,0)]
   ):
    cv2.circle(
     procedure_proj_img_bgr,
     tuple(np.rint(cross_pt).astype("int")),
     3,
     color,
     -1,
     cv2.CV_AA
    )
   # Rotated image
   procedure_rot_img_bgr = rot_img_bgr.copy()
   cv2.line(
    procedure_rot_img_bgr,
    tuple(np.rint(rot_middle_ellipse_center).astype("int")),
    tuple(np.rint(rot_shadow_ellipse_center).astype("int")),
    (255, 0, 0),
    1,
    cv2.CV_AA
   )
   rot_north_angle_rad = 0
   cv2.fillConvexPoly(
    procedure_rot_img_bgr,
    np.rint(np.array([
    rot_middle_ellipse_center,
    rot_middle_ellipse_center + middle_ellipse_height/2. * np.array([
     np.cos(rot_north_angle_rad+np.radians(3)),
     np.sin(rot_north_angle_rad+np.radians(3))
    ]),
    rot_middle_ellipse_center + (15+middle_ellipse_height/2.) * np.array([
     np.cos(rot_north_angle_rad),
     np.sin(rot_north_angle_rad)
    ]),
    rot_middle_ellipse_center + middle_ellipse_height/2. * np.array([
     np.cos(rot_north_angle_rad-np.radians(3)),
     np.sin(rot_north_angle_rad-np.radians(3))
    ])
    ])).astype("int"),
    (0, 0, 255),
    cv2.CV_AA
   )
   cv2.putText(
    procedure_rot_img_bgr,
    "N",
    tuple(np.rint(
     [20, 5] + rot_middle_ellipse_center + middle_ellipse_height/2. * np.array([
      np.cos(rot_north_angle_rad),
      np.sin(rot_north_angle_rad)
     ])
    ).astype("int")),
    cv2.FONT_HERSHEY_PLAIN,
    1,
    (0, 0, 255),
    1,
    cv2.CV_AA
   )
   cv2.ellipse(
    procedure_rot_img_bgr,
    (
     rot_middle_ellipse_center,
     (middle_ellipse_height, middle_ellipse_height),
     np.degrees(middle_ellipse_rot_rad)
    ),
    (0, 0, 255),
    1,
    cv2.CV_AA
   )
   cv2.ellipse(
    procedure_rot_img_bgr,
    cv2.fitEllipse(rot_shadow_ellipse_points),
    (255, 0, 0),
    1,
    cv2.CV_AA
   )
   cv2.circle(
    procedure_rot_img_bgr,
    tuple(np.rint(rot_shadow_ellipse_center).astype("int")),
    1,
    (255, 0, 0),
    -1,
    cv2.CV_AA
   )
   cv2.circle(
    procedure_rot_img_bgr,
    tuple(np.rint(rot_middle_ellipse_center).astype("int")),
    1,
    (0, 0, 255),
    -1,
    cv2.CV_AA
   )
   for cross_pt, color in zip(
    rot_middle_ellipse_cross_points,
    [(255, 255, 0), (0, 255, 255), (255, 0, 255), (0, 255,0)]
   ):
    cv2.circle(
     procedure_rot_img_bgr,
     tuple(np.rint(cross_pt).astype("int")),
     3,
     color,
     -1,
     cv2.CV_AA
    )

   procedure_img_bgr = np.zeros( (272*2 + 10, 320*2 + 10, 3), "uint8")
   procedure_img_bgr[0:272,0:320] = img_bgr
   procedure_img_bgr[0:272,330:] = procedure_marked_img_bgr
   procedure_img_bgr[282:,0:320] = procedure_proj_img_bgr
   procedure_img_bgr[282:,330:] = procedure_rot_img_bgr
   
   cv2.putText(
    procedure_img_bgr,
    "1. Original",
    (15, 30),
    cv2.FONT_HERSHEY_COMPLEX,
    1,
    (255, 255, 255),
    2,
    cv2.CV_AA
   )
   cv2.putText(
    procedure_img_bgr,
    "2. Marked",
    (330+15, 30),
    cv2.FONT_HERSHEY_COMPLEX,
    1,
    (255, 255, 255),
    2,
    cv2.CV_AA
   )
   cv2.putText(
    procedure_img_bgr,
    "3. Projected",
    (15, 282+30),
    cv2.FONT_HERSHEY_COMPLEX,
    1,
    (255, 255, 255),
    2,
    cv2.CV_AA
   )
   cv2.putText(
    procedure_img_bgr,
    "4. Rotated/Final",
    (330+15, 282+30),
    cv2.FONT_HERSHEY_COMPLEX,
    1,
    (255, 255, 255),
    2,
    cv2.CV_AA
   )
   cv2.imshow("procedure preview", procedure_img_bgr)
   if not cmd_args.no_save and cmd_args.save_procedure:
    cv2.imwrite(
     "{path}/procedure.{fi}.png".format(
     path = cmd_args.output_dir,
     fi = procedure_index
     ),
     procedure_img_bgr
    )
    procedure_index += 1
  
  
  if cv2.waitKey(cmd_args.preview_pause) % 256 == 27:
   break 
  
 # Expected Analemma
 if not cmd_args.no_save and cmd_args.save_centers:
  expected_centers_data_file = open(
   "{path}/expected_analemma_centers.data".format(path = cmd_args.output_dir),
   "w"
  )
  expected_centers_data_file.write(
   "# sol, solar_longitude (deg), shadow_center_x (mm), shadow_center_y (mm)\n"
  )
  
 expected_cur = readable_connection.cursor()
 expected_cur.execute(
  r"""
  WITH temp_table AS(
   SELECT DISTINCT ON(pds_headers_v.sol)
    pds_headers_v.sol,
    pds_headers_v.solar_longitude::double precision,
    pds_headers_v.sfd_solar_azimuth::double precision as solar_azimuth,
    pds_headers_v.sfd_solar_elevation::double precision as solar_elevation,
    ref_images.elps_middle as middle_ellipse_rrect
   FROM
    pds_headers_v
    JOIN image_regs USING(id)
    JOIN ref_images ON(image_regs.ref_id = ref_images.id)
   WHERE
    pds_headers_v.lmst BETWEEN
     %(target_lmst)s::interval - %(target_lmst_err)s AND
     %(target_lmst)s::interval + %(target_lmst_err)s
    AND pds_headers_v.host_id = %(host_id)s
   ORDER BY
    pds_headers_v.sol,
    abs(extract(EPOCH FROM pds_headers_v.lmst - %(target_lmst)s))
   )
   SELECT * from temp_table ORDER BY sol;
  """,
  images_query_opts
 )
 for row in expected_cur:
  mm_to_pixels = row["middle_ellipse_rrect"][1][1]/55.
  h = 54 * mm_to_pixels
  expected_shadow_center = np.array([
   320/2 + h * np.cos(np.radians(row["solar_azimuth"])) / np.tan(np.radians(row["solar_elevation"])),
   272/2 + h * np.sin(np.radians(row["solar_azimuth"])) / np.tan(np.radians(row["solar_elevation"]))
  ])
  
  if not cmd_args.no_save and cmd_args.save_centers:
   shadow_center_from_center = 1./mm_to_pixels * (expected_shadow_center - [320/2, 272/2])
   expected_centers_data_file.write(
    "{:} {:} {:} {:}\n".format(
     row["sol"],
     row["solar_longitude"],
     shadow_center_from_center[0],
     -shadow_center_from_center[1]
    )
   )
  cv2.circle(
   prev_out_img_bgr,
   tuple(np.rint(2 * expected_shadow_center).astype("int")),
   2,
   (255, 255, 255),
   -1,
   cv2.CV_AA
  )
 if not cmd_args.no_save and not cmd_args.no_save_animation:
  for j in xrange(0, 2*(cmd_args.transition_frames+1)):
   cv2.imwrite(
    "{path}/animation.{fi}.png".format(
     path = cmd_args.output_dir,
     fi = frame_index
    ),
    prev_out_img_bgr
   )
   frame_index += 1
   cv2.imshow("animation preview", prev_out_img_bgr)
 
 if not cmd_args.no_save and cmd_args.save_centers:
  measured_centers_data_file.close()
  expected_centers_data_file.close()
  
 # Generate plots
 if not cmd_args.no_save and cmd_args.plots:
  print "Generating plots..."
  measured_data = np.loadtxt(
   "{:}/measured_analemma_centers.data".format(cmd_args.output_dir),
   ndmin = 2
  )
  expected_data = np.loadtxt(
   "{:}/expected_analemma_centers.data".format(cmd_args.output_dir),
   ndmin = 2
  )
  expected_data_m = expected_data[np.in1d(expected_data[:,1], measured_data[:,1])]
  error_figure = plt.figure(figsize=(16,9))
  error_ax = error_figure.add_subplot(111)
  error_ax.set_title(
   "Distance Between Expected & Measured Shadow Centers ({:})".format(
    "Opportunity" if cmd_args.host_id == "MER1" else "Spirit"
   )
  )
  error_ax.set_xlabel("Solar Longitude (deg)")
  error_ax.set_ylabel("Distance (mm)")
  error_ax.grid()
  error_ax.scatter(
   measured_data[:,1],
   np.sqrt(np.sum((expected_data_m[:,2:4] - measured_data[:,2:4])**2, axis=1))
  )
  error_ax.set_xticks(xrange(0, 380, 20))
  error_ax.set_xlim(-5, 365)
  error_ax.set_ylim(bottom=-5)
  error_figure.savefig(
   "{:}/{:}_expected_measured_distance.svg".format(
    cmd_args.output_dir,
    cmd_args.host_id
   ),
   bbox_inches = "tight"
  )
  
  analemma_figure = plt.figure(figsize=(16,9))
  analemma_ax = analemma_figure.add_subplot(111)
  ticker = MultipleLocator(10)
  analemma_ax.xaxis.set_major_locator(ticker)
  analemma_ax.yaxis.set_major_locator(ticker)
  analemma_ax.set_title(
   "Measured & Expected Shadow Centers ({:})".format(
    "Opportunity" if cmd_args.host_id == "MER1" else "Spirit"
   )
  )
  analemma_ax.set_xlabel("mm")
  analemma_ax.set_ylabel("mm")
  analemma_ax.grid(True)
  analemma_ax.axvline(color = "black")
  analemma_ax.axhline(color = "black")
  scatter = analemma_ax.scatter(
   measured_data[:,2],
   measured_data[:,3],
   c = measured_data[:,1],
   s = 100,
   linewidth = 0,
   cmap =  plt.get_cmap("hsv"),
   vmin = 0,
   vmax = 360,
   label = "Measured"
  )
  analemma_ax.scatter(
   expected_data[:,2],
   expected_data[:,3],
   c = "black",
   s = 25,
   marker = ".",
   label = "Expected"
  )
  clb = analemma_figure.colorbar(scatter, aspect=40, pad=.02)
  clb.set_label("Solar Longitude (deg)")
  
  analemma_ax.legend()
  analemma_ax.set_xlim(-50, 50)
  analemma_ax.set_ylim(-30, 30)
  analemma_ax.set_aspect(1)
  analemma_figure.savefig(
   "{:}/{:}_expected_measured_analemma.svg".format(
    cmd_args.output_dir,
    cmd_args.host_id
   ),
   bbox_inches = "tight"
  )
 
 print "Finished."
  
  
