# Gurugram sector price map

Interactive map of Gurugram sectors coloured by the median premium-developer asking price (₹ per sq ft, super area), with the projects and source links behind every number. Live at **https://gagan86nagpal.github.io/gurgaon-map/**

## What's in here

| Path | What it is |
|---|---|
| `index.html` | The published page (same as `gurgaon-price-map-standalone.html`). Self-contained; open it locally too. |
| `agent_*.json` | The price evidence — one row per project quote: sector, project, developer, ₹/sq ft min–max, basis, status, source URL, as-of month. |
| `sectors.json` | Sector polygons/points projected to the map's coordinate system (built by `build_geo.py`). |
| `osm/` | Raw OpenStreetMap Overpass pulls: sector boundaries, roads, metro routes, IGI footprint, Delhi border, landmarks, societies, parks/golf courses. |
| `build_geo.py` | Filters and stitches the OSM sector relations into `sectors.json`. |
| `build_html.py` | Builds the page: aggregates quotes per sector, draws roads/metro/landmarks, embeds the search index. |

## Rebuild

```bash
python3 build_geo.py      # only if osm/sectors_geom.json or osm/nodes.json changed
python3 build_html.py     # writes gurgaon-price-map.html and gurgaon-price-map-standalone.html
cp gurgaon-price-map-standalone.html index.html
```

To add price evidence, append rows to a new `agent_<anything>.json` following the existing schema and rebuild.

## How the numbers work

Each project's quoted ₹/sq ft is reduced to a midpoint. A sector's range is the lowest to highest project midpoint; its colour is the median. Quotes are asking prices from portals, developer sites, news and (flagged) broker microsites — not registered transaction values. The ₹ crore ticket sizes are the sector range × an editable typical super area (2 BHK 1,350 · 3 BHK 1,900 · 4 BHK 2,800 sq ft).

Map data © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors, ODbL. Not investment advice; verify any quote against the project's RERA registration.
