from pmtiles.reader import Reader
from fastapi import Request
from pmtiles.tile import Compression
from typing import Optional
import boto3

s3_client = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",  # Use service name from docker-compose
    aws_access_key_id="user",
    aws_secret_access_key="password",
    # region_name='us-east-1'
)


class S3RangeReader:
    """
    Custom reader class that implements range requests for PMTiles using S3 API
    """

    def __init__(self, bucket: str, key: str, s3_client=None):
        self.bucket = bucket
        self.key = key
        self.s3 = s3_client
        self._header: Optional[bytes] = None
        self._length: Optional[int] = None

    def length(self) -> int:
        """Get total file length"""
        if self._length is None:
            response = self.s3.head_object(Bucket=self.bucket, Key=self.key)
            self._length = response["ContentLength"]
        return self._length

    def get_bytes(self, offset: int, length: int) -> bytes:
        """
        Get specific byte range from S3

        Args:
            offset: Start byte position
            length: Number of bytes to read
        """
        response = self.s3.get_object(
            Bucket=self.bucket,
            Key=self.key,
            Range=f"bytes={offset}-{offset + length - 1}",
        )
        return response["Body"].read()


def get_tile_json(
    bucket: str, key: str, request: Request
) -> dict[str, str | int | float]:
    range_reader = S3RangeReader(bucket, key + ".pmtiles", s3_client=s3_client)
    reader = Reader(get_bytes=range_reader.get_bytes)
    metadata = reader.metadata()
    first_vector_layer = metadata["vector_layers"][0]
    # reader.
    tilejson = {
        "tilejson": "3.0.0",
        "name": metadata.get("name", "PMTiles"),
        "description": metadata.get("description", ""),
        "version": metadata.get("version", "1.0.0"),
        "attribution": metadata.get("attribution", ""),
        "type": "vector" if metadata["format"] == "pbf" else "raster",
        "format": metadata["format"],
        "bounds": metadata.get("bounds", []),
        "center": metadata.get("center", []),
        "minzoom": first_vector_layer.get("minzoom", 0),
        "maxzoom": first_vector_layer.get("maxzoom", 20),
        "tiles": [
            str(
                request.url_for("get_tile", dataset=f"{key}", z="{z}", x="{x}", y="{y}")
            )
            # + f"?url={url}"
        ],
    }
    return tilejson


def get_tile(bucket: str, key: str, z: int, x: int, y: int) -> Optional[bytes]:
    """
    Get a specific tile from a PMTiles file in S3
    """
    # Create the range reader
    range_reader = S3RangeReader(bucket, key, s3_client=s3_client)

    # Create PMTiles reader with our custom range reader
    reader = Reader(range_reader.get_bytes)

    # Initialize the reader (this will fetch the header using range request)
    # await reader.init()

    # Get the specific tile (this will make range requests as needed)
    tile_data = reader.get(z, x, y)

    return tile_data
