import geopandas as gpd
from shapely.geometry import Point, Polygon, MultiPoint
from shapely.ops import voronoi_diagram
import numpy as np
import pandas as pd
import duckdb
import subprocess

conn = duckdb.connect("./data/markets.db")


# Function to create a grid of points within a polygon
def generate_grid_within_polygon_vectorized(gdf: gpd.GeoDataFrame, spacing: float):
    # Get bounds for all polygons
    bounds = gdf.geometry.total_bounds  # [minx, miny, maxx, maxy]
    minx, miny, maxx, maxy = bounds

    # Generate a grid of points covering the entire bounding box
    x_coords = np.arange(minx, maxx, spacing)
    y_coords = np.arange(miny, maxy, spacing)
    grid_points = np.array(np.meshgrid(x_coords, y_coords)).T.reshape(-1, 2)

    # Convert grid points to a GeoDataFrame
    grid_gdf = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(grid_points[:, 0], grid_points[:, 1]),
        crs=gdf.crs,
    )

    # Perform a spatial join to keep only points within the polygons
    points_within_polygons = gpd.sjoin(grid_gdf, gdf, predicate="intersects")

    return points_within_polygons


# Load the input GeoJSON containing polygons
input_geojson = "./data/zcta/zcta.geojson"  # Replace with your file path
polygons_gdf: gpd.GeoDataFrame = gpd.GeoDataFrame(gpd.read_file(input_geojson))

polygons_gdf["geometry"] = polygons_gdf["geometry"].buffer(0)
# exclude AK, HI, Guam, PR


backbone_df = conn.query("""
    CREATE OR REPLACE TABLE geo_details AS
    SELECT *
    FROM './data/iad.GeographicDetails.csv';


    SELECT
        DISTINCT value.unnest as postal_code
    FROM geo_details t1,
        UNNEST(string_split(postalCodes, ',')) AS value;
""").to_df()


polygons_gdf = polygons_gdf.loc[
    polygons_gdf.zip_code.isin(backbone_df.postal_code.tolist())
]

# union = polygons_gdf.geometry.union_all()
# hull = union.convex_hull
# union_gdf = gpd.GeoDataFrame(geometry=[union], crs=polygons_gdf.crs)
# hull_gdf = gpd.GeoDataFrame(geometry=[hull], crs=polygons_gdf.crs)
# overlaid = gpd.overlay(hull_gdf, union_gdf, how="difference")

# Create a grid of points for each polygon
spacing = 0.05  # Adjust spacing as needed

grid_points = generate_grid_within_polygon_vectorized(polygons_gdf, spacing)


# Generate Voronoi polygons from the points
multipoint = MultiPoint(grid_points.geometry.tolist())
voronoi_result = voronoi_diagram(
    multipoint, envelope=polygons_gdf.geometry.union_all(), edges=False
)

voronoi_gdf: gpd.GeoDataFrame = gpd.GeoDataFrame(
    geometry=list(voronoi_result.geoms),
    crs=grid_points.crs,
)

voronoi_gdf: gpd.GeoDataFrame = voronoi_gdf.sjoin(
    grid_points[polygons_gdf.columns], predicate="contains"
)
us_outline = gpd.read_file(
    "https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_nation_20m.zip",
    driver="ESRI Shapefile",
)

voronoi_gdf: gpd.GeoDataFrame = voronoi_gdf.clip(us_outline.geometry)

voronoi_gdf: gpd.GeoDataFrame = voronoi_gdf.overlay(polygons_gdf, how="difference")

merged = gpd.GeoDataFrame(pd.concat([polygons_gdf, voronoi_gdf], ignore_index=True))

merged = merged.dissolve(by="zip_code")


# Convert Voronoi polygons to a GeoDataFrame and save as GeoPackage

merged.to_file("./data/output_voronoi.gpkg", driver="GPKG")
print("Voronoi polygons saved to ./data/output_voronoi.gpkg")

dissolve_query = """
    INSTALL spatial;
    LOAD spatial;
    CREATE OR REPLACE TABLE geo_details AS
    SELECT *
    FROM './data/iad.GeographicDetails.csv';
    CREATE OR REPLACE TABLE markets_long AS
    SELECT t1.* EXCLUDE postalCodes,
        value.unnest as postal_code
    FROM geo_details t1,
        UNNEST(string_split(postalCodes, ',')) AS value;
    CREATE OR REPLACE TABLE zip_voronoi as
    SELECT *
    FROM ST_READ(
            './data/output_voronoi.gpkg'
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

"""

conn.execute(dissolve_query)


subprocess.run(
    """
    tippecanoe -o ./data/submarket.pmtiles --simplification 4 \
    -l submarket \
    --no-tiny-polygon-reduction --maximum-tile-bytes 5000000 \
    --limit-tile-feature-count 1006343 -Z 0 -zg \
    ./submarket.fgb
"""
)

subprocess.run(
    """
    tippecanoe -o ./data/market.pmtiles --simplification 4 \
    -l market \
    --no-tiny-polygon-reduction --maximum-tile-bytes 5000000 \
    --limit-tile-feature-count 1006343 -Z 0 -zg \
    ./market.fgb
"""
)
