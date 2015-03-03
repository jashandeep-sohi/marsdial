CREATE TABLE pds_files(
 id text PRIMARY KEY,
 headers_json json,
 image_py bytea
);

COMMENT ON TABLE pds_files IS 'This table contains the content of the original PDS files.';
COMMENT ON COLUMN pds_files.id IS 'A unique identification string. The value is extracted from the PDS header PRODUCT_ID.';
COMMENT ON COLUMN pds_files.headers_json IS 'A PDS headers as a JSON object.';
COMMENT ON COLUMN pds_files.image_py IS 'The extracted image from the PDS file for use in python. The image is stored as a numpy array, then it is pickled and finally compressed using bz2.';
