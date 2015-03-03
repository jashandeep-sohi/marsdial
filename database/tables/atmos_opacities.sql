CREATE TABLE atmos_opacities(
 id text PRIMARY KEY,
 sol integer,
 host_id text,
 filter_name text,
 ltst time without time zone,
 solar_longitude numeric,
 solar_distance numeric,
 airmass numeric,
 solar_flux numeric, 
 atmos_opacity numeric,
 atmos_opacity_err numeric
);

COMMENT ON TABLE atmos_opacities IS 'This table contains atmospheric opacities provided by Mark Lemmon.';
COMMENT ON COLUMN atmos_opacities.id IS 'Product ID of the image used to calculate the opacity.';
COMMENT ON COLUMN atmos_opacities.sol IS 'Sol.';
COMMENT ON COLUMN atmos_opacities.host_id IS 'Rover ID.';
COMMENT ON COLUMN atmos_opacities.filter_name IS 'Filter name.';
COMMENT ON COLUMN atmos_opacities.ltst IS 'Local True Solar Time';
COMMENT ON COLUMN atmos_opacities.solar_longitude IS 'Martian season in degrees past northern spring equinox.';
COMMENT ON COLUMN atmos_opacities.solar_distance IS 'Mars-Sun distance in AU at time of observation.';
COMMENT ON COLUMN atmos_opacities.airmass IS 'Airmass factor relative to the zenith. It can be approximated as the secant of zenith angle for most observations, but is computed using a 13-km scale height to improve accuracy for low-Sun observations.';
COMMENT ON COLUMN atmos_opacities.solar_flux IS 'Observed solar flux in DN ms-1 after subtracting background light. Computed using Pancam calibration parameters. A value of -1.0 indicates an image that resulted in a non-measurement opacity (e.g., due to missing packet and/or data saturation).';
COMMENT ON COLUMN atmos_opacities.atmos_opacity IS 'Measured atmospheric opacity using the current best relative calibration. A value of -1.0 indicates an image that resulted in a non-measurement opacity (e.g., due to missing packet and/or data saturation).';
COMMENT ON COLUMN atmos_opacities.atmos_opacity_err IS 'Relative error in the opacity measurement. A value of -1.0 indicates an image that resulted in a non-measurement opacity (e.g., due to missing packet and/or data saturation).';


CREATE VIEW atmos_opacities_v AS
 SELECT
  atmos_opacities.*,
  split_part(atmos_opacities.filter_name, '_', 2) as filter_id,
  split_part(atmos_opacities.filter_name, '_', 3) as filter_wavelength
 FROM
  atmos_opacities;
  
COMMENT ON VIEW atmos_opacities_v IS 'This view adds some convinence columns to the atmos_opacities table.';
COMMENT ON COLUMN atmos_opacities_v.filter_id IS 'Two letters for the filter side & number.';
COMMENT ON COLUMN atmos_opacities_v.filter_wavelength IS 'Bandpass wavelength of the filter.';

