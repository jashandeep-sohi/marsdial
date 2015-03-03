CREATE TABLE shadow_pos(
 id text PRIMARY KEY REFERENCES pds_files ON DELETE CASCADE,
 elps_rrect json
);

COMMENT ON TABLE shadow_pos IS 'This table contains info about the shadown in each image.';
COMMENT ON COLUMN shadow_pos.id IS 'PDS header PRODUCT_ID';
COMMENT ON shadow_pos.elps_rrect IS 'A json encoded rotated rectange enclosing the shadow ellipse See opencv definition. [center, size, angle].'
