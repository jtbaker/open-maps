INSTALL spatial;
LOAD spatial;
CREATE OR REPLACE TABLE geo_details AS
SELECT *
FROM '/Users/jasonbaker/Downloads/iad.GeographicDetails.csv';
CREATE OR REPLACE TABLE markets_long AS
SELECT t1.* EXCLUDE postalCodes,
    value.unnest as postal_code
FROM geo_details t1,
    UNNEST(string_split(postalCodes, ',')) AS value;
CREATE OR REPLACE TABLE zip_voronoi as
SELECT *
FROM ST_READ(
        './output_voronoi.gpkg'
    );
CREATE OR REPLACE TABLE voronoi_with_submarket_info AS
SELECT v.*,
    m.*
FROM zip_voronoi v
    JOIN markets_long m ON v.zip_code = m.postal_code
WHERE m.type = 'submarket';
CREATE OR REPLACE TABLE voronoi_with_market_info AS
SELECT v.*,
    m.*
FROM zip_voronoi v
    JOIN markets_long m ON v.zip_code = m.postal_code
WHERE type = 'market';
COPY (
    SELECT ST_MAKEVALID(ST_BUFFER(ST_UNION_AGG(geom), 0)) geometry,
        code,
        type
    FROM voronoi_with_submarket_info
    GROUP BY code,
        type
) TO './submarket.fgb' WITH (FORMAT GDAL, DRIVER 'FlatGeoBuf');
COPY (
    SELECT ST_MAKEVALID(ST_BUFFER(ST_UNION_AGG(geom), 0)) geometry,
        code,
        type
    FROM voronoi_with_market_info
    GROUP BY code,
        type
) TO './market.fgb' WITH (FORMAT GDAL, DRIVER 'FlatGeoBuf');