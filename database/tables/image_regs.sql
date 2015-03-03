CREATE TABLE image_regs(
 id text PRIMARY KEY REFERENCES pds_files ON DELETE CASCADE,
 r numeric,
 dx numeric,
 dy numeric,
 ref_id text REFERENCES ref_images(id) ON DELETE CASCADE
);

COMMENT ON TABLE image_regs IS 'This table contains the image registration values.';
COMMENT ON COLUMN ref_images.id IS 'PDS header PRODUCT_ID.';
COMMENT ON COLUMN image_regs.r IS 'A measure of how good the registration is (r=1 is perfect)';
COMMENT ON COLUMN image_regs.dx IS 'Shift in x.';
COMMENT ON COLUMN image_regs.dy IS 'Shift in y.';
COMMENT ON COLUMN image_regs.ref_id IS 'Shifts are relative to this reference image.';

