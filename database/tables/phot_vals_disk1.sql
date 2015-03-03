CREATE TABLE phot_vals_disk1(
 id text PRIMARY KEY REFERENCES pds_files ON DELETE CASCADE,
 shadow_mean numeric,
 light_mean numeric,
 shadow_std numeric,
 light_std numeric,
 shadow_pixels integer,
 light_pixels integer
);

COMMENT ON TABLE phot_vals_disk1 IS 'This table contains photometry values measured only in the outer disk region.';
COMMENT ON COLUMN phot_vals_disk1.id IS 'PDS header PRODUCT_ID';
COMMENT ON COLUMN phot_vals_disk1.shadow_mean IS 'Mean pixel intensity in the region shadowed by the MarsDial gnomon.';
COMMENT ON COLUMN phot_vals_disk1.light_mean IS 'Mean pixel intensity in the region not shadowed by the MarsDial gnomon.';
COMMENT ON COLUMN phot_vals_disk1.shadow_std IS 'Standard deviation of the pixel intensity in the region shadowed by the MarsDial gnomon.';
COMMENT ON COLUMN phot_vals_disk1.light_std IS 'Standard deviation of the pixel intensity in the region not shadowed by the MarsDial gnomon.';
COMMENT ON COLUMN phot_vals_disk1.shadow_pixels IS 'Number of pixels in the region shadowed by the MarsDial gnomon.';
COMMENT ON COLUMN phot_vals_disk1.light_pixels IS 'Number of pixels in the region not shadowed by the MarsDial gnomon.';

