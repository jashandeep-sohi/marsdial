CREATE TABLE ref_images(
 id text PRIMARY KEY REFERENCES pds_files ON DELETE CASCADE,
 elps_outer json,
 elps_middle json,
 elps_earth json,
 elps_mars json,
 poly_roi1 json,
 poly_earth json,
 poly_mars json,
 poly_post json
);
 
COMMENT ON TABLE ref_images IS 'This table contains reference images and different regions of interest in each.';
COMMENT ON COLUMN ref_images.id IS 'PDS header PRODUCT_ID.';
COMMENT ON COLUMN ref_images.elps_outer IS 'Outer ellipse.';
COMMENT ON COLUMN ref_images.elps_middle IS 'Middle ellipse.';
COMMENT ON COLUMN ref_images.elps_earth IS 'Earth ellipse.';
COMMENT ON COLUMN ref_images.elps_mars IS 'Mars ellipse.';
COMMENT ON COLUMN ref_images.poly_roi1 IS 'A list of points enclosing the outer disk.';
COMMENT ON COLUMN ref_images.poly_earth IS 'A list of points enclosing earth.';
COMMENT ON COLUMN ref_images.poly_mars IS 'A list of points enclosing mars.';
COMMENT ON COLUMN ref_images.poly_post IS 'A list of points enclosing the post.';
  
