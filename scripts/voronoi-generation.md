\*\*\* To generate the voronoi polygons, run this command from the root of the repo:

docker build . -f ./scripts/VoronoiDockerfile -t voronoi-build

docker run -v $(pwd)/data:/app/data voronoi-build
