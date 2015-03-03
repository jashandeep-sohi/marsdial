CREATE TABLE pds_headers(
 id text PRIMARY KEY REFERENCES pds_files ON DELETE CASCADE,
 sol integer,
 img_width integer,
 img_height integer,
 host_id text,
 filter_name text,
 ltst time without time zone,
 lmst time without time zone,
 solar_longitude numeric,
 rfd_inst_azimuth numeric,
 rfd_inst_elevation numeric,
 sfd_inst_azimuth numeric,
 sfd_inst_elevation numeric,
 sfd_solar_azimuth numeric,
 sfd_solar_elevation numeric,
 radiance_offset numeric,
 radiance_scaling_factor numeric,
 rcs_rotation_quaternion numeric[4]
);

COMMENT ON TABLE pds_headers IS 'This table contains PDS headers of interest.';
COMMENT ON COLUMN pds_headers.id IS 'PDS header PRODUCT_ID.';
COMMENT ON COLUMN pds_headers.sol IS 'PDS header PLANET_DAY_NUMBER.';
COMMENT ON COLUMN pds_headers.img_width IS 'PDS header IMAGE->LINE_SAMPLES.';
COMMENT ON COLUMN pds_headers.img_height IS 'PDS header IMAGE->LINES.';
COMMENT ON COLUMN pds_headers.host_id IS 'PDS header INSTRUMENT_HOST_ID.';
COMMENT ON COLUMN pds_headers.filter_name IS 'PDS header INSTRUMENT_STATE_PARMS->FILTER_NAME.';
COMMENT ON COLUMN pds_headers.ltst IS 'PDS header LOCAL_TRUE_SOLAR_TIME.';
COMMENT ON COLUMN pds_headers.lmst IS 'Derived header. Calculated local mean solar time.';
COMMENT ON COLUMN pds_headers.solar_longitude IS 'PDS header SOLAR_LONGITUDE.';
COMMENT ON COLUMN pds_headers.rfd_inst_azimuth IS 'PDS header ROVER_DERIVED_GEOMETRY_PARMS->INSTRUMENT_AZIMUTH.';
COMMENT ON COLUMN pds_headers.rfd_inst_elevation IS 'PDS header ROVER_DERIVED_GEOMETRY_PARMS->INSTRUMENT_ELEVATION.';
COMMENT ON COLUMN pds_headers.sfd_inst_azimuth IS 'PDS header SITE_DERIVED_GEOMETRY_PARM->INSTRUMENT_AZIMUTH.';
COMMENT ON COLUMN pds_headers.sfd_inst_elevation IS 'PDS header SITE_DERIVED_GEOMETRY_PARM->INSTRUMENT_ELEVATION.';
COMMENT ON COLUMN pds_headers.sfd_solar_azimuth IS 'PDS header SITE_DERIVED_GEOMETRY_PARM->SOLAR_AZIMUTH.';
COMMENT ON COLUMN pds_headers.sfd_solar_elevation IS 'PDS header SITE_DERIVED_GEOMETRY_PARM->SOLAR_ELEVATION.';
COMMENT ON COLUMN pds_headers.radiance_offset IS 'PDS header DERIVED_IMAGE_PARMS->RADIANCE_OFFSET.';
COMMENT ON COLUMN pds_headers.rcs_rotation_quaternion IS 'PDS header ROVER_COORDINATE_SYSTEM->ORIGIN_ROTATION_QUATERNION.';

CREATE VIEW pds_headers_v AS
 SELECT
  pds_headers.*,
  split_part(pds_headers.filter_name, '_', 2) as filter_id,
  split_part(pds_headers.filter_name, '_', 3) as filter_wavelength
 FROM
  pds_headers;
  
COMMENT ON VIEW pds_headers_v IS 'This view adds some convinence columns to the pds_headers table.';
COMMENT ON COLUMN pds_headers_v.filter_id IS 'Two letters for the filter side & number.';
COMMENT ON COLUMN pds_headers_v.filter_wavelength IS 'Bandpass wavelength of the filter.';

CREATE OR REPLACE FUNCTION calc_roll(rotation_quaternion numeric[4])
 RETURNS double precision
 LANGUAGE SQL
 IMMUTABLE
 AS $def$
 SELECT atan2(2.0 * ($1[1] * $1[2] + $1[3] * $1[4]), 1.0 - 2.0 * ($1[2]^2 + $1[3]^2));
 $def$;
COMMENT ON FUNCTION calc_roll(rotation_quaternion numeric[4]) IS 'Calculates roll in radians using a rotation quaternion.';

CREATE OR REPLACE FUNCTION calc_pitch(rotation_quaternion numeric[4])
 RETURNS double precision
 LANGUAGE SQL
 IMMUTABLE
 AS $def$
 SELECT asin(-2.0 * ($1[1] * $1[3] - $1[4] * $1[2]));
 $def$;
COMMENT ON FUNCTION calc_pitch(rotation_quaternion numeric[4]) IS 'Calculates pitch in radians using a rotation quaternion.';
 
CREATE OR REPLACE FUNCTION calc_yaw(rotation_quaternion numeric[4])
 RETURNS double precision
 LANGUAGE SQL
 IMMUTABLE
 AS $def$
 SELECT atan2(2.0 * ($1[1] * $1[4] + $1[2] * $1[3]), 1.0 - 2.0 * ($1[3]^2 + $1[4]^2));
 $def$;
COMMENT ON FUNCTION calc_yaw(rotation_quaternion numeric[4]) IS 'Calculates yaw in radians using a rotation quaternion.'; 
