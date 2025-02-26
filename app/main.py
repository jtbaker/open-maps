import boto3
from fastapi import FastAPI, HTTPException, Request, Path, Query
from fastapi.responses import Response, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pmtiles.tile import Compression

# from pmtiles.reader import Reader
import aiofiles
import os
from core.pmtiles_helpers import get_tile as get_tile_sync, get_tile_json
from aiopmtiles import Reader
from pmtiles.reader import Reader

app = FastAPI(title="Vector Tile Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure S3 client to use LocalStack
s3 = boto3.client(
    "s3",
    endpoint_url="http://localstack:4566",  # Use service name from docker-compose
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1",
)

BUCKET_NAME = "tiles-bucket"
PMTILES_KEY = "zcta.pmtiles"
LOCAL_PMTILES_PATH = "./data/tiles.pmtiles"


async def download_pmtiles():
    """Download PMTiles file from S3 if it doesn't exist locally"""
    if not os.path.exists(LOCAL_PMTILES_PATH):
        try:
            s3.download_file(BUCKET_NAME, PMTILES_KEY, LOCAL_PMTILES_PATH)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to download PMTiles: {str(e)}"
            )


# @app.on_event("startup")
# async def startup_event():
#     """Initialize the PMTiles reader on startup"""
#     await download_pmtiles()


@app.get("/{dataset}/tilejson.json")
def get_tilejson(
    request: Request, dataset: str = Path(..., description="Dataset name")
):
    """
    Serve TileJSON metadata for the PMTiles archive.
    """
    return get_tile_json("pmtiles", f"{dataset}", request)


@app.get("/tiles/{dataset}/{z}/{x}/{y}")
def get_tile(
    dataset: str = Path(..., description="Dataset name"),
    z: int = Path(...),
    x: int = Path(...),
    y: int = Path(...),
):
    """Serve vector tiles from PMTiles archive"""
    try:
        res = get_tile_sync("pmtiles", f"{dataset}.pmtiles", z, x, y)

        return Response(
            content=res,
            headers={"content-encoding": "gzip", "cache-control": "max-age=3600"},
            media_type="application/vnd.mapbox-vector-tile",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tile: {str(e)}")
        # Ensure PMTiles file exists
        # if not os.path.exists(LOCAL_PMTILES_PATH):
        #     await download_pmtiles()

        # async with aiofiles.open(LOCAL_PMTILES_PATH, 'rb') as f:
        #     reader = Reader(await f.read())
        #     tile_data = reader.get(z, x, y)

        #     if tile_data is None:
        #         raise HTTPException(status_code=404, detail="Tile not found")

        #     return Response(
        #         content=tile_data,
        #         media_type="application/x-protobuf",
        #         headers={
        #             "Content-Type": "application/x-protobuf",
        #             "Content-Encoding": "gzip"
        #         }
        #     )
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


'''
from fastapi import FastAPI, Path, Query, Request
from starlette.responses import Response
from aiopmtiles import Reader
from pmtiles.tile import Compression

app = FastAPI()

# Endpoint to serve TileJSON
@app.get("/tilejson.json")
async def get_tilejson(
    request: Request,
    url: str = Query(..., description="URL to the PMTiles archive")
):
    """
    Serve TileJSON metadata for the PMTiles archive.
    """
    async with Reader(url) as reader:
        metadata = await reader.metadata()
        tilejson = {
            "tilejson": "3.0.0",
            "name": metadata.get("name", "PMTiles"),
            "description": metadata.get("description", ""),
            "version": metadata.get("version", "1.0.0"),
            "attribution": metadata.get("attribution", ""),
            "type": "vector" if reader.header.is_vector else "raster",
            "format": "pbf" if reader.header.is_vector else "png",
            "bounds": reader.header.bounds,
            "minzoom": reader.header.min_zoom,
            "maxzoom": reader.header.max_zoom,
            "tiles": [
                str(request.url_for("get_tile", z="{z}", x="{x}", y="{y}")) + f"?url={url}"
            ],
        }
        return tilejson


# Endpoint to serve individual tiles
@app.get("/tiles/{z}/{x}/{y}", response_class=Response)
async def get_tile(
    z: int = Path(..., ge=0, le=30, description="Zoom level"),
    x: int = Path(..., description="Tile column"),
    y: int = Path(..., description="Tile row"),
    url: str = Query(..., description="URL to the PMTiles archive")
):
    """
    Serve individual tiles (Z/X/Y) from the PMTiles archive.
    """
    headers = {}
    async with Reader(url) as reader:
        data = await reader.get_tile(z, x, y)
        if reader.header.internal_compression == Compression.GZIP:
            headers["Content-Encoding"] = "gzip"
        return Response(data, media_type="application/x-protobuf", headers=headers)
'''
