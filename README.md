# Tiles

FastAPI tile service serving configured Cloud Optimized GeoTIFF layers as TMS/XYZ and WMTS.

The app registers only these TileMatrixSets:

- `NetherlandsRDNewQuad` for `EPSG:28992`
- `WebMercatorQuad` for `EPSG:3857`
- `WorldCRS84Quad` for `EPSG:4326`

## Config

The app reads `config.json` by default. This file is ignored by git so local COG URLs are not committed.

Copy the example and edit it locally:

```bash
cp config.example.json config.json
```

Set `TITILER_CONFIG` to read a different file.

```json
{
  "title": "Tiles",
  "layers": [
    {
      "name": "example_layer",
      "url": "cog://https://example.com/path/to/cog.tif"
    }
  ]
}
```

Layer names may contain only letters, numbers, underscores, and hyphens.

## Run

This project uses `uv` with Python pinned in `pyproject.toml`.

```bash
uv sync
uv run uvicorn app.main:app --reload
```

The app root redirects to the web UI at `http://127.0.0.1:8000/tiles`.

Open `http://127.0.0.1:8000/docs` for the API docs.

Run lint checks with:

```bash
uv run ruff check .
```

## Useful Endpoints

- Web UI: `http://127.0.0.1:8000/tiles`
- Layers JSON: `http://127.0.0.1:8000/layers`
- Service metadata: `http://127.0.0.1:8000/metadata`
- TMS list: `http://127.0.0.1:8000/tileMatrixSets`
- Layer map viewer: `http://127.0.0.1:8000/tiles/lufo_2025/NetherlandsRDNewQuad/map.html`
- Layer TileJSON: `http://127.0.0.1:8000/tiles/lufo_2025/NetherlandsRDNewQuad/tilejson.json?tile_format=png`
- Layer TMS/XYZ tile URL template: `http://127.0.0.1:8000/tiles/lufo_2025/tiles/NetherlandsRDNewQuad/{z}/{x}/{y}.png`
- Layer WMTS capabilities: `http://127.0.0.1:8000/tiles/lufo_2025/WMTSCapabilities.xml?TileMatrixSetId=NetherlandsRDNewQuad&tile_format=png`

## Docker

The Docker image is a multi-stage build. Build dependencies such as `gcc` and `libc6-dev` are only installed in the builder stage; the runtime stage runs as `www-data`.
The runtime trusts proxy forwarding headers so generated URLs use the original client scheme from headers such as `X-Forwarded-Proto`.

Build and run with the example config baked into the image:

```bash
docker build -t tiles .
docker run --rm -p 8000:8000 tiles
```

Run with a runtime config mounted from the host:

```bash
docker run --rm -p 8000:8000 \
  -v "$PWD/config.json:/config/config.json:ro" \
  tiles
```

## Notes

- The public `cog://` URI is kept in layer metadata, while the raster reader receives the underlying HTTPS URL.
- The TileMatrixSet bounds are the standard Dutch RD New grid extent: `-285401.92,22598.08,595401.92,903401.92`.
