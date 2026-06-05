import json
from pathlib import Path

GEOJSON_DIR = Path("outputs/geojson")
TILE_NAME = "austin_demo"
INPUT_GEOJSON = GEOJSON_DIR / f"{TILE_NAME}_footprints.geojson"
OUTPUT_HTML = GEOJSON_DIR / "map.html"


def build_map(geojson_path: Path, output_path: Path):
    print(f"[read] {geojson_path}")

    with open(geojson_path) as f:
        geojson_data = json.load(f)

    feature_count = len(geojson_data.get("features", []))
    print(f"  Features: {feature_count:,} building footprints")

    geojson_str = json.dumps(geojson_data, separators=(",", ":"))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Aerial Building Footprint Extractor</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background: #0f0f0f; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; overflow: hidden; }}

    #header {{
      position: fixed; top: 0; left: 0; right: 0; z-index: 100;
      background: rgba(10,10,10,0.93); backdrop-filter: blur(8px);
      padding: 12px 20px; display: flex; align-items: center; gap: 16px;
      border-bottom: 1px solid #222;
    }}
    #header h1 {{ font-size: 14px; font-weight: 600; color: #fff; letter-spacing: 0.03em; }}
    .badge {{
      font-size: 11px; padding: 3px 8px; border-radius: 4px;
      background: #0f2e1a; color: #4ade80; border: 1px solid #166534;
    }}
    #stats {{
      margin-left: auto; display: flex; gap: 24px; font-size: 12px; color: #666;
    }}
    #stats b {{ color: #e0e0e0; }}

    #canvas-wrap {{
      position: fixed; top: 49px; left: 0; right: 0; bottom: 0;
      overflow: hidden; background: #1a1e1a;
      display: flex; align-items: center; justify-content: center;
    }}
    canvas {{ cursor: grab; }}
    canvas:active {{ cursor: grabbing; }}

    #tooltip {{
      position: fixed; display: none; background: rgba(10,10,10,0.92);
      border: 1px solid #333; border-radius: 5px; padding: 8px 12px;
      font-size: 12px; color: #ccc; pointer-events: none; z-index: 200;
    }}
    #tooltip b {{ color: #4ade80; }}

    #legend {{
      position: fixed; bottom: 20px; right: 20px; z-index: 100;
      background: rgba(10,10,10,0.92); border: 1px solid #222;
      border-radius: 6px; padding: 12px 16px; font-size: 12px;
    }}
    #legend .title {{ font-weight: 600; margin-bottom: 8px; color: #fff; font-size: 11px; letter-spacing: 0.05em; text-transform: uppercase; }}
    .leg-item {{ display: flex; align-items: center; gap: 8px; margin: 5px 0; color: #888; }}
    .swatch {{ width: 12px; height: 12px; border-radius: 2px; flex-shrink: 0; }}

    #controls {{
      position: fixed; bottom: 20px; left: 20px; z-index: 100;
      display: flex; gap: 8px;
    }}
    .btn {{
      background: rgba(10,10,10,0.92); border: 1px solid #333;
      color: #aaa; padding: 6px 12px; border-radius: 4px;
      cursor: pointer; font-size: 12px; transition: all 0.15s;
    }}
    .btn:hover {{ background: #1a1a1a; color: #fff; border-color: #555; }}
  </style>
</head>
<body>

<div id="header">
  <h1>Aerial Building Footprint Extractor</h1>
  <div class="badge">SAM ViT-B &nbsp;·&nbsp; GPU</div>
  <div class="badge" style="background:#1a1a2e;color:#818cf8;border-color:#3730a3;">GeoJSON Output</div>
  <div id="stats">
    <div>Footprints &nbsp;<b>{feature_count}</b></div>
    <div>Model &nbsp;<b>SAM ViT-B</b></div>
    <div>Source &nbsp;<b>Synthetic Aerial</b></div>
  </div>
</div>

<div id="canvas-wrap">
  <canvas id="c"></canvas>
</div>

<div id="tooltip"></div>

<div id="controls">
  <button class="btn" onclick="resetView()">⌖ Reset View</button>
  <button class="btn" onclick="toggleLabels()">⊞ Labels</button>
</div>

<div id="legend">
  <div class="title">Legend</div>
  <div class="leg-item"><div class="swatch" style="background:#22c55e;opacity:0.5;border:1px solid #16a34a;"></div>Detected footprint</div>
  <div class="leg-item"><div class="swatch" style="background:#16a34a;"></div>Selected footprint</div>
  <div class="leg-item"><div class="swatch" style="background:#2d3a2d;"></div>Ground / background</div>
</div>

<script>
const geojson = {geojson_str};
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
const wrap = document.getElementById('canvas-wrap');
const tooltip = document.getElementById('tooltip');

// Collect all coordinates to compute bounds
let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
geojson.features.forEach(f => {{
  const rings = f.geometry.type === 'Polygon' ? f.geometry.coordinates : f.geometry.coordinates.flat();
  rings[0].forEach(([x, y]) => {{
    minX = Math.min(minX, x); minY = Math.min(minY, y);
    maxX = Math.max(maxX, x); maxY = Math.max(maxY, y);
  }});
}});

const DATA_W = maxX - minX;
const DATA_H = maxY - minY;

let scale = 1, offsetX = 0, offsetY = 0;
let showLabels = false;
let selectedId = null;
let isDragging = false, dragStart = null, dragOffset = null;

function resize() {{
  canvas.width = wrap.clientWidth;
  canvas.height = wrap.clientHeight;
  resetView(false);
  draw();
}}

function resetView(redraw = true) {{
  const pad = 60;
  const sx = (canvas.width - pad * 2) / DATA_W;
  const sy = (canvas.height - pad * 2) / DATA_H;
  scale = Math.min(sx, sy);
  offsetX = (canvas.width - DATA_W * scale) / 2 - minX * scale;
  offsetY = (canvas.height - DATA_H * scale) / 2 - minY * scale;
  if (redraw) draw();
}}

function toScreen(x, y) {{
  return [x * scale + offsetX, y * scale + offsetY];
}}

function toData(sx, sy) {{
  return [(sx - offsetX) / scale, (sy - offsetY) / scale];
}}

// Area → color gradient (small=cool, large=warm)
function footprintColor(area, selected) {{
  if (selected) return {{ fill: 'rgba(74,222,128,0.75)', stroke: '#86efac', strokeW: 2 }};
  const t = Math.min(area / 15000, 1);
  const r = Math.round(30 + t * 60);
  const g = Math.round(180 - t * 60);
  const b = Math.round(80 - t * 40);
  return {{
    fill: `rgba(${{r}},${{g}},${{b}},0.45)`,
    stroke: `rgba(${{r+30}},${{g+30}},${{b+30}},0.9)`,
    strokeW: 1
  }};
}}

function drawPolygon(coords) {{
  const [fx, fy] = toScreen(coords[0][0], coords[0][1]);
  ctx.moveTo(fx, fy);
  for (let i = 1; i < coords.length; i++) {{
    const [sx, sy] = toScreen(coords[i][0], coords[i][1]);
    ctx.lineTo(sx, sy);
  }}
  ctx.closePath();
}}

function draw() {{
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Background grid (subtle)
  ctx.strokeStyle = '#1f271f';
  ctx.lineWidth = 0.5;
  const step = 100 * scale;
  const gox = offsetX % step;
  const goy = offsetY % step;
  for (let x = gox; x < canvas.width; x += step) {{
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
  }}
  for (let y = goy; y < canvas.height; y += step) {{
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
  }}

  // Draw footprints
  geojson.features.forEach(f => {{
    const id = f.properties.building_id;
    const area = f.properties.area_m2;
    const selected = id === selectedId;
    const col = footprintColor(area, selected);
    const rings = f.geometry.type === 'Polygon'
      ? f.geometry.coordinates
      : f.geometry.coordinates.flat();

    ctx.beginPath();
    rings.forEach(ring => drawPolygon(ring));
    ctx.fillStyle = col.fill;
    ctx.fill('evenodd');
    ctx.strokeStyle = col.stroke;
    ctx.lineWidth = col.strokeW;
    ctx.stroke();

    // Label
    if (showLabels && scale > 0.3) {{
      const cx = rings[0].reduce((s, p) => s + p[0], 0) / rings[0].length;
      const cy = rings[0].reduce((s, p) => s + p[1], 0) / rings[0].length;
      const [sx, sy] = toScreen(cx, cy);
      ctx.fillStyle = 'rgba(200,255,200,0.85)';
      ctx.font = `${{Math.max(9, 11 * scale)}}px monospace`;
      ctx.textAlign = 'center';
      ctx.fillText(`#${{id}}`, sx, sy);
    }}
  }});

  // Scale bar
  const barPx = 100;
  const barUnits = Math.round(barPx / scale);
  ctx.fillStyle = '#555';
  ctx.fillRect(canvas.width - 140, canvas.height - 36, barPx, 3);
  ctx.fillStyle = '#888';
  ctx.font = '10px monospace';
  ctx.textAlign = 'center';
  ctx.fillText(`${{barUnits}} px`, canvas.width - 140 + barPx / 2, canvas.height - 42);
}}

function toggleLabels() {{
  showLabels = !showLabels; draw();
}}

// Hit test
function hitTest(mx, my) {{
  const [dx, dy] = toData(mx, my);
  for (let i = geojson.features.length - 1; i >= 0; i--) {{
    const f = geojson.features[i];
    const rings = f.geometry.type === 'Polygon'
      ? f.geometry.coordinates
      : f.geometry.coordinates.flat();
    ctx.beginPath();
    rings.forEach(ring => drawPolygon(ring));
    if (ctx.isPointInPath(mx, my)) return f;
  }}
  return null;
}}

canvas.addEventListener('mousemove', e => {{
  if (isDragging) {{
    offsetX = dragOffset[0] + (e.clientX - dragStart[0]);
    offsetY = dragOffset[1] + (e.clientY - dragStart[1]);
    draw(); return;
  }}
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  const hit = hitTest(mx, my);
  if (hit) {{
    canvas.style.cursor = 'pointer';
    tooltip.style.display = 'block';
    tooltip.style.left = (e.clientX + 14) + 'px';
    tooltip.style.top = (e.clientY - 10) + 'px';
    tooltip.innerHTML = `<b>Building #${{hit.properties.building_id}}</b><br>Area: ${{hit.properties.area_m2.toLocaleString()}} m²`;
  }} else {{
    canvas.style.cursor = 'grab';
    tooltip.style.display = 'none';
  }}
}});

canvas.addEventListener('mousedown', e => {{
  isDragging = true;
  dragStart = [e.clientX, e.clientY];
  dragOffset = [offsetX, offsetY];
}});

canvas.addEventListener('mouseup', e => {{
  if (!isDragging) return;
  const moved = Math.abs(e.clientX - dragStart[0]) + Math.abs(e.clientY - dragStart[1]);
  isDragging = false;
  if (moved < 4) {{
    const rect = canvas.getBoundingClientRect();
    const hit = hitTest(e.clientX - rect.left, e.clientY - rect.top);
    selectedId = hit ? hit.properties.building_id : null;
    draw();
  }}
}});

canvas.addEventListener('wheel', e => {{
  e.preventDefault();
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  const delta = e.deltaY > 0 ? 0.85 : 1.18;
  offsetX = mx - (mx - offsetX) * delta;
  offsetY = my - (my - offsetY) * delta;
  scale *= delta;
  draw();
}}, {{ passive: false }});

window.addEventListener('resize', resize);
resize();
</script>
</body>
</html>"""

    output_path.write_text(html, encoding="utf-8")
    print(f"[saved] {output_path}")
    print(f"  Open: file:///{output_path.resolve().as_posix()}")


def main():
    print("=== Building Footprint Map Visualizer ===\n")
    if not INPUT_GEOJSON.exists():
        raise FileNotFoundError(f"GeoJSON not found: {INPUT_GEOJSON}\nRun vectorize.py first.")
    build_map(INPUT_GEOJSON, OUTPUT_HTML)
    print("\n[complete] Pipeline done.")


if __name__ == "__main__":
    main()