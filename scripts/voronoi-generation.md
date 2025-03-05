\*\*\* To generate the voronoi polygons, run this command from the root of the repo:

Make sure that you have both /data/zcta/zcta.geojson and /data/iad.GeographicDetails.csv available in your /data directory that will be bind mounted into the container.

docker build . -f ./scripts/VoronoiDockerfile -t voronoi-build

docker run -v $(pwd)/data:/app/data voronoi-build
