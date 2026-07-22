# Tiles

FastAPI tile service serving configured Cloud Optimized GeoTIFF layers as TMS/XYZ and WMTS.

The app registers only the Dutch RD New TileMatrixSet:

- `EPSG:28992`

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
  "nodata_color": "#ffffff",
  "layers": [
    {
      "name": "example_layer",
      "url": "cog://https://example.com/path/to/cog.tif"
    }
  ]
}
```

Layer names may contain only letters, numbers, underscores, and hyphens.
Set `nodata_color` globally or per layer as `"#RRGGBB"` or `[r, g, b]` to make pixels matching that output color transparent.
Set `nodata_color_tolerance` to allow near matches per RGB channel; for example, `8` makes `#f7f7f7` through `#ffffff` transparent when `nodata_color` is `#ffffff`.

## Run

This project uses `uv` with Python pinned in `pyproject.toml`.

Install dependencies and create a local config file:

```bash
uv sync
cp config.example.json config.json
```

Start the app:

```bash
uv run python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

If your environment cannot write to the default `uv` cache directory, keep the cache inside the project:

```bash
UV_CACHE_DIR=.uv-cache uv sync
UV_CACHE_DIR=.uv-cache uv run python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

For local development in an environment that supports file watching, add `--reload`.

The app root redirects to the web UI at `http://127.0.0.1:8000/tiles`.

Open `http://127.0.0.1:8000/docs` for the API docs.

Run lint checks with:

```bash
uv run ruff check .
```

Or, with a workspace-local `uv` cache:

```bash
UV_CACHE_DIR=.uv-cache uv run ruff check .
```

## Useful Endpoints

- Web UI: `http://127.0.0.1:8000/tiles`
- Layers JSON: `http://127.0.0.1:8000/layers`
- Service metadata: `http://127.0.0.1:8000/metadata`
- TMS list: `http://127.0.0.1:8000/tiles/tileMatrixSets`
- Layer map viewer: `http://127.0.0.1:8000/tiles/lufo_2025/EPSG:28992/map.html`
- Layer TileJSON: `http://127.0.0.1:8000/tiles/lufo_2025/EPSG:28992/tilejson.json?tile_format=png`
- Layer TMS/XYZ tile URL template: `http://127.0.0.1:8000/tiles/lufo_2025/tiles/EPSG:28992/{z}/{x}/{y}.png`
- Layer WMTS capabilities: `http://127.0.0.1:8000/tiles/lufo_2025/WMTSCapabilities.xml?TileMatrixSetId=EPSG:28992&tile_format=png`

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
