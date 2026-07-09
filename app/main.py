"""Config-driven tile service for COG layers."""

import json
import os
import re
from html import escape
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from morecantile import TileMatrixSet, TileMatrixSets, tms
from pyproj import CRS
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers
from titiler.core.factory import TilerFactory, TMSFactory
from titiler.extensions.wmts import wmtsExtension

CONFIG_PATH = Path(os.environ.get("TITILER_CONFIG", "config.json"))
TMS_ID = "NetherlandsRDNewQuad"
LAYER_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def normalize_cog_url(url: str) -> str:
    """Return the URL rio-tiler should read."""
    return url.removeprefix("cog://")


def load_config(path: Path) -> dict[str, Any]:
    """Load and validate the layer config."""
    with path.open() as src:
        config = json.load(src)

    layers = config.get("layers")
    if not isinstance(layers, list) or not layers:
        raise ValueError("config.json must contain a non-empty 'layers' array")

    layer_names: set[str] = set()
    for layer in layers:
        if not isinstance(layer, dict):
            raise ValueError("each layer must be an object")

        name = layer.get("name")
        url = layer.get("url")
        if not isinstance(name, str) or not LAYER_NAME_RE.fullmatch(name):
            raise ValueError(
                "each layer needs a 'name' containing only letters, numbers, underscores, or hyphens"
            )
        if name in layer_names:
            raise ValueError(f"duplicate layer name: {name}")
        if not isinstance(url, str) or not url:
            raise ValueError(f"layer '{name}' needs a non-empty 'url'")

        layer_names.add(name)

    return config


def path_dependency_for(url: str):
    """Build a dependency returning a fixed layer URL."""

    def path_dependency() -> str:
        return normalize_cog_url(url)

    return path_dependency


def configured_layers() -> list[dict[str, str]]:
    """Return configured layers with useful endpoint templates."""
    return [
        {
            "name": layer["name"],
            "map": f"/tiles/{layer['name']}/{TMS_ID}/map.html",
            "info": f"/tiles/{layer['name']}/info",
            "tilejson": f"/tiles/{layer['name']}/{TMS_ID}/tilejson.json?tile_format=png",
            "tiles": f"/tiles/{layer['name']}/tiles/{TMS_ID}/{{z}}/{{x}}/{{y}}.png",
            "wmts": (
                f"/tiles/{layer['name']}/WMTSCapabilities.xml"
                f"?TileMatrixSetId={TMS_ID}&tile_format=png"
            ),
        }
        for layer in config["layers"]
    ]


def tiles_landing_html() -> str:
    """Render the layer landing page."""
    title = escape(config.get("title", "Tiles"))
    layer_cards = "".join(
        f"""
        <article class="layer-card">
          <div class="layer-head">
            <span class="icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 18 3 21V6l6-3 6 3 6-3v15l-6 3-6-3Z" />
                <path d="M9 3v15" />
                <path d="M15 6v15" />
              </svg>
            </span>
            <div class="card-text">
              <strong>{escape(layer['name'])}</strong>
              <small>TMS and WMTS endpoints for this configured raster layer.</small>
            </div>
          </div>
          <div class="actions">
            <a class="primary" href="{escape(layer['map'])}">Open map</a>
            <a href="{escape(layer['info'])}">Info</a>
          </div>
          <label>Available projections</label>
          <div class="projection-list">
            <a href="/tileMatrixSets/NetherlandsRDNewQuad">EPSG:28992</a>
            <a href="/tileMatrixSets/WebMercatorQuad">EPSG:3857</a>
            <a href="/tileMatrixSets/WorldCRS84Quad">EPSG:4326</a>
          </div>
          <div class="endpoint-list">
            <div>
              <label>TMS / XYZ</label>
              <p>Use this URL template in clients that support XYZ or TileJSON.</p>
              <code>{escape(layer['tiles'])}</code>
              <a class="endpoint-link" href="{escape(layer['tilejson'])}">Open TileJSON</a>
            </div>
            <div>
              <label>WMTS</label>
              <p>Use this capabilities document in clients that support WMTS.</p>
              <code>{escape(layer['wmts'])}</code>
              <a class="endpoint-link" href="{escape(layer['wmts'])}">Open WMTS capabilities</a>
            </div>
          </div>
        </article>
        """
        for layer in configured_layers()
    )
    return f"""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{title}</title>
        <style>
          :root {{
            --purple: #5047e5;
            --bg: #f4f4fc;
            --card: #fff;
            --border: #d8d8df;
            --text: #08080a;
            --muted: #6b7280;
            --orange: #a85228;
            --yellow: #fff4bf;
            --green: #e8ffb7;
          }}
          * {{ box-sizing: border-box; }}
          body {{
            margin: 0;
            min-height: 100vh;
            font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            color: var(--text);
            background: var(--bg);
          }}
          .topbar {{
            height: 60px;
            display: flex;
            align-items: center;
            padding: 0 46px;
            color: #fff;
            background: var(--purple);
            box-shadow: 0 1px 0 rgba(0,0,0,0.08);
          }}
          .brand {{ display: flex; align-items: center; gap: 12px; font-weight: 800; }}
          .brand {{ font-size: 1.5rem; }}
          .brand svg {{ width: 24px; height: 24px; }}
          main {{ width: min(1420px, calc(100% - 48px)); margin: 0 auto; padding: 58px 0 68px; }}
          section {{ margin-bottom: 58px; }}
          h1 {{ margin: 0 0 26px; font-size: 1.75rem; line-height: 1.1; letter-spacing: -0.04em; }}
          .grid {{ display: grid; grid-template-columns: repeat(4, minmax(220px, 1fr)); gap: 16px; }}
          .layers-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 16px; }}
          .card {{
            min-height: 82px;
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 16px;
            border: 1px solid var(--border);
            border-radius: 6px;
            background: var(--card);
            color: var(--text);
            text-decoration: none;
            transition: border-color 120ms ease, box-shadow 120ms ease, transform 120ms ease;
          }}
          .card:hover {{ border-color: #b8b8c4; box-shadow: 0 12px 28px rgba(31, 41, 55, 0.08); transform: translateY(-1px); }}
          .layer-card {{
            min-height: 82px;
            padding: 18px;
            border: 1px solid var(--border);
            border-radius: 6px;
            background: var(--card);
            color: var(--text);
          }}
          .layer-head {{ display: flex; align-items: center; gap: 16px; margin-bottom: 18px; }}
          .layer-card.compact .layer-head {{ margin-bottom: 14px; }}
          .icon {{
            width: 48px;
            height: 48px;
            flex: 0 0 auto;
            display: grid;
            place-items: center;
            border-radius: 999px;
            background: var(--yellow);
            color: var(--orange);
          }}
          .icon.green {{ background: var(--green); color: #236245; }}
          .icon svg {{ width: 25px; height: 25px; }}
          .card-text {{ display: grid; gap: 2px; min-width: 0; }}
          .card strong {{ font-size: 1.12rem; line-height: 1.2; }}
          .card small, .layer-card small {{ color: var(--muted); font-weight: 600; }}
          .actions {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 0 0 16px; }}
          .actions a {{
            display: inline-flex;
            align-items: center;
            min-height: 36px;
            padding: 8px 12px;
            border: 1px solid var(--border);
            border-radius: 999px;
            color: var(--text);
            background: #fff;
            text-decoration: none;
            font-weight: 750;
          }}
          .actions a.primary {{ background: var(--purple); border-color: var(--purple); color: #fff; }}
          .endpoint-list {{ display: grid; gap: 18px; }}
          .endpoint-list p {{ margin: 0 0 8px; color: var(--muted); font-size: 0.95rem; }}
          .projection-list {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 18px; }}
          .projection-list a {{
            padding: 7px 10px;
            border-radius: 999px;
            background: #fff8d9;
            color: var(--orange);
            text-decoration: none;
            font-weight: 800;
            font-size: 0.9rem;
          }}
          label {{ display: block; color: var(--muted); font-size: 0.78rem; font-weight: 800; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.08em; }}
          code {{ display: block; padding: 12px 14px; border-radius: 6px; background: #f7f7fb; border: 1px solid var(--border); color: #2f3340; overflow-x: auto; }}
          .endpoint-link {{ display: inline-block; margin-top: 8px; color: var(--purple); font-weight: 800; text-decoration: none; }}
          @media (max-width: 1100px) {{ .grid {{ grid-template-columns: repeat(2, minmax(220px, 1fr)); }} }}
          @media (max-width: 640px) {{
            .topbar {{ padding: 0 18px; }}
            .brand {{ font-size: 1.2rem; }}
            main {{ width: min(100% - 28px, 1420px); padding-top: 34px; }}
            .grid, .layers-grid {{ grid-template-columns: 1fr; }}
          }}
        </style>
      </head>
      <body>
        <header class="topbar">
          <div class="brand">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z" />
            </svg>
            <span>Tiles</span>
          </div>
        </header>
        <main>
          <section>
            <div class="layers-grid">{layer_cards}</div>
          </section>
        </main>
      </body>
    </html>
    """


netherlands_rd_new = TileMatrixSet.custom(
    # National Dutch RD New tiling extent used by the standard EPSG:28992 WMTS grid.
    (-285401.92, 22598.08, 595401.92, 903401.92),
    CRS.from_epsg(28992),
    id=TMS_ID,
    matrix_scale=[1, 1],
)

supported_tms = TileMatrixSets(
    {
        TMS_ID: netherlands_rd_new,
        "WebMercatorQuad": tms.get("WebMercatorQuad"),
        "WorldCRS84Quad": tms.get("WorldCRS84Quad"),
    }
)

config = load_config(CONFIG_PATH)
tms_factory = TMSFactory(supported_tms=supported_tms)

app = FastAPI(
    title=config.get("title", "Tiles"),
    description="Serves configured COG layers as TMS and WMTS.",
)


@app.middleware("http")
async def hide_source_urls(request, call_next):
    """Prevent configured source URLs from leaking in generated XML responses."""
    response = await call_next(request)
    if not request.url.path.endswith("/WMTSCapabilities.xml"):
        return response

    body = b""
    async for chunk in response.body_iterator:
        body += chunk

    text = body.decode("utf-8")
    text = text.replace(
        "<ows:Title>Web Map Tile Service by TiTiler</ows:Title>",
        "<ows:Title>Web Map Tile Service</ows:Title>",
    )
    text = text.replace("<ows:ProviderName>TiTiler</ows:ProviderName>", "")
    for layer in config["layers"]:
        layer_name = layer["name"]
        for source in {layer["url"], normalize_cog_url(layer["url"])}:
            text = text.replace(f"{source}_", f"{layer_name}_")
            text = text.replace(source, layer_name)

    headers = dict(response.headers)
    headers.pop("content-length", None)
    return Response(
        content=text,
        status_code=response.status_code,
        headers=headers,
        media_type=response.media_type or "application/xml",
    )

for layer in config["layers"]:
    layer_name = layer["name"]
    router = APIRouter()
    tiler = TilerFactory(
        router=router,
        router_prefix=f"/tiles/{layer_name}",
        path_dependency=path_dependency_for(layer["url"]),
        supported_tms=supported_tms,
        extensions=[wmtsExtension()],
    )
    app.include_router(tiler.router, prefix=f"/tiles/{layer_name}", tags=[f"Layer: {layer_name}"])

app.include_router(tms_factory.router, tags=["TileMatrixSets"])
add_exception_handlers(app, DEFAULT_STATUS_CODES)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    """Start clients at the configured layer list."""
    return RedirectResponse(url="/tiles")


@app.get("/tiles", response_class=HTMLResponse, tags=["Service"])
def tiles_landing_page() -> HTMLResponse:
    """Return the configured layer landing page."""
    return HTMLResponse(tiles_landing_html())


@app.get("/layers", tags=["Service"])
def list_layers() -> dict[str, Any]:
    """Return configured layers and their endpoint templates."""
    return {"layers": configured_layers()}


@app.get("/metadata", tags=["Service"])
def service_metadata() -> dict[str, str]:
    """Return service metadata and the most useful endpoints."""
    return {
        "config": str(CONFIG_PATH),
        "layers": "/layers",
        "tiles_ui": "/tiles",
        "tile_matrix_set": TMS_ID,
        "tile_matrix_sets": "/tileMatrixSets",
        "docs": "/docs",
    }
