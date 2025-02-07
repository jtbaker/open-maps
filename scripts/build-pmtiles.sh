#/bin/zsh

# curl -L https://www2.census.gov/geo/tiger/GENZ2023/gdb/cb_2023_us_all_5m.zip
# unzip cb_2023_us_all_5m.zip -d cb_2023_us_all_5m
# census bureau website was broken when i was doing this 🕵️


# gsutil -m cp 'gs://jtb-open-data/zcta-csv-*.gz' ./data
# for file in ./data/*.gz; do
#     # gunzip $file ./data/${file%.gz}.csv
#     gunzip -c "$file" > ${file%.gz}.csv
#     rm $file
# done


query=$(cat <<EOF
INSTALL spatial; 
LOAD spatial; 
COPY (
    SELECT lpad(zip_code::text, 5, '0') zip_code, 
    * exclude (zip_code,zip_code_geom), 
    ST_GEOMFROMTEXT(zip_code_geom) geometry 
    FROM read_csv('./data/zcta-csv-*.csv.gz')
) 
    TO './data/zcta/zcta.geojson' WITH (FORMAT GDAL, DRIVER 'GeoJSON');
EOF
)

duckdb -c "$query"


tippecanoe -o ./data/zcta/zcta.pmtiles --simplification 4 --no-tiny-polygon-reduction --maximum-tile-bytes 5000000 --limit-tile-feature-count 1006343 -Z 3 -zg ./data/zcta/zcta.geojson
