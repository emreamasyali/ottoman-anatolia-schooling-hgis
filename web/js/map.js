/**
 * map.js — Ottoman Anatolia Schooling HGIS
 * Interactive Leaflet web map
 *
 * Layers:
 *   1. Kaza boundaries – choropleth by Christian share (1881 census)
 *   2. Missionary stations – all ABC-FM stations & outstations
 *   3. Main missionary stations – the 10 principal stations
 *   4. Armenian schools – geocoded from 1901 Maarif Salnamesi
 *   5. Christian buildings – churches & chapels (OpenStreetMap + historical)
 *   6. Commercial centers – major Ottoman trade hubs
 *
 * Data files live in ../data/derived/ (GeoJSON) and are loaded with fetch().
 * The map is fully static and deployable via GitHub Pages.
 */

'use strict';

// ── Config ───────────────────────────────────────────────────────────────────

const DATA_BASE = '../data/derived/geojson/';

const LAYERS_CONFIG = {
  kazas:           { file: 'kazas_boundaries.geojson',            label: 'Kaza boundaries' },
  locations:       { file: 'missionary_locations.geojson',        label: 'All missionary locations' },
  mainStations:    { file: 'main_missionary_stations.geojson',    label: 'Main stations' },
  armenian:        { file: 'armenian_schools.geojson',            label: 'Armenian schools' },
  christian:       { file: 'christian_buildings.geojson',         label: 'Christian buildings' },
  commercial:      { file: 'commercial_centers.geojson',          label: 'Commercial centers' },
};

// Choropleth breaks for ChristianShare (0–1)
const CHOROPLETH_BREAKS = [0, 0.02, 0.05, 0.10, 0.20, 0.35, 1.01];
const CHOROPLETH_COLORS = ['#0f3460','#1a4a7a','#1d6fa8','#2994d4','#6ab8e8','#b8dff5','#e8f8ff'];

// Point style presets
const POINT_STYLES = {
  locations:    { color: '#ff9f43', radius: 5,  label: 'Missionary location' },
  mainStations: { color: '#ff4757', radius: 8,  label: 'Main station' },
  armenian:     { color: '#a29bfe', radius: 4,  label: 'Armenian school' },
  christian:    { color: '#55efc4', radius: 3,  label: 'Christian building' },
  commercial:   { color: '#ffeaa7', radius: 7,  label: 'Commercial center' },
};

// ── State ────────────────────────────────────────────────────────────────────

// Ottoman 1899 historical map overlay config
const OTTOMAN_OVERLAY = {
  url: 'img/ottoman_1899_overlay.jpg',
  bounds: [[29.3468, 23.4149], [42.9966, 48.1760]],  // [[S,W],[N,E]] WGS84
  opacity: 0.6,
};

const state = {
  map: null,
  leafletLayers: {},   // key → Leaflet layer object
  geojsonData: {},     // key → raw GeoJSON
  visible: {
    kazas: true, locations: true, mainStations: true,
    armenian: true, christian: false, commercial: true,
    ottoman1899: false,
  },
};

// ── Init map ─────────────────────────────────────────────────────────────────

function initMap() {
  state.map = L.map('map', {
    center: [38.5, 35.5],
    zoom: 6,
    minZoom: 4,
    maxZoom: 14,
    zoomControl: true,
  });

  // Base tile layer — CartoDB dark
  L.tileLayer(
    'https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png',
    {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors ' +
        '&copy; <a href="https://carto.com/">CARTO</a>',
      subdomains: 'abcd',
      maxZoom: 19,
    }
  ).addTo(state.map);

  // Label overlay on top
  L.tileLayer(
    'https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png',
    { subdomains: 'abcd', maxZoom: 19, pane: 'shadowPane' }
  ).addTo(state.map);
}

// ── Choropleth helpers ────────────────────────────────────────────────────────

function choroplethColor(share) {
  for (let i = 0; i < CHOROPLETH_BREAKS.length - 1; i++) {
    if (share < CHOROPLETH_BREAKS[i + 1]) return CHOROPLETH_COLORS[i];
  }
  return CHOROPLETH_COLORS[CHOROPLETH_COLORS.length - 1];
}

function kazaStyle(feature) {
  const share = feature.properties.ChristianShare;
  const fill = (share != null && !isNaN(share))
    ? choroplethColor(share)
    : '#1a1a2e';
  return {
    fillColor: fill,
    fillOpacity: 0.7,
    color: '#3a4060',
    weight: 0.8,
    opacity: 0.9,
  };
}

// ── Popup builders ────────────────────────────────────────────────────────────

function kazaPopup(feature) {
  const p = feature.properties;
  const share = p.ChristianShare != null
    ? (p.ChristianShare * 100).toFixed(1) + '%'
    : 'N/A';
  const armShare = p.ArmenianShare != null
    ? (p.ArmenianShare * 100).toFixed(1) + '%'
    : 'N/A';
  const total = p.GrandTotal != null
    ? Number(p.GrandTotal).toLocaleString()
    : 'N/A';

  return `
    <h4>${p.kaza || p.RTENO || 'Kaza'}</h4>
    <span class="tag" style="background:#1d6fa844;color:#6ab8e8;">Kaza</span>
    <table>
      <tr><td>Vilayet</td><td>${p.Vilayet || '—'}</td></tr>
      <tr><td>Sanjak</td><td>${p.Sanjak || '—'}</td></tr>
      <tr><td>Total pop. (1881)</td><td>${total}</td></tr>
      <tr><td>Christian share</td><td>${share}</td></tr>
      <tr><td>Armenian share</td><td>${armShare}</td></tr>
      <tr><td>Kaz. code</td><td>${p.kazcode || p.RTENO || '—'}</td></tr>
    </table>`;
}

function locationPopup(feature) {
  const p = feature.properties;
  const isMain = p.MainStation == 1;
  const isOut  = p.OutStation  == 1;
  const kind   = isMain ? 'Main Station' : isOut ? 'Outstation' : 'Station';
  const tagCol = isMain ? '#ff4757' : '#ff9f43';
  const year   = p.DateFounded ? String(p.DateFounded).split('.')[0] : '—';
  return `
    <h4>${p.Name || 'Missionary Location'}</h4>
    <span class="tag" style="background:${tagCol}22;color:${tagCol};">${kind}</span>
    <table>
      <tr><td>Founded</td><td>${year}</td></tr>
      <tr><td>Dep. station</td><td>${p.Dependent || '—'}</td></tr>
      <tr><td>Notes</td><td>${p.Note || '—'}</td></tr>
    </table>`;
}

function stationPopup(feature) {
  const p = feature.properties;
  const isMain  = p.MainStation == 1;
  const isOut   = p.OutStation  == 1;
  const kind    = isMain ? 'Main Station' : isOut ? 'Outstation' : 'Station';
  const tagCol  = isMain ? '#ff4757' : isOut ? '#ff9f43' : '#fdcb6e';

  return `
    <h4>${p.Name || 'Station'}</h4>
    <span class="tag" style="background:${tagCol}22;color:${tagCol};">${kind}</span>
    <table>
      <tr><td>Mission</td><td>${p.Mission || '—'}</td></tr>
      <tr><td>Kaza</td><td>${p.Kaza || '—'}</td></tr>
      <tr><td>Sanjak</td><td>${p.Sanjak || '—'}</td></tr>
      <tr><td>Vilayet</td><td>${p.Vilayet || '—'}</td></tr>
      <tr><td>Modern name</td><td>${p.ModernName || '—'}</td></tr>
      <tr><td>Dep. station</td><td>${p.Dependent || '—'}</td></tr>
      <tr><td>Variations</td><td>${p.Variations || '—'}</td></tr>
    </table>`;
}

function armenianSchoolPopup(feature) {
  const p = feature.properties;
  return `
    <h4>${p.name || p.properti_1 || 'Armenian School'}</h4>
    <span class="tag" style="background:#a29bfe22;color:#a29bfe;">Armenian school</span>
    <table>
      <tr><td>Type</td><td>${p.type_detail || p.type || '—'}</td></tr>
      <tr><td>Location</td><td>${p.location || p.properti_3 || '—'}</td></tr>
      <tr><td>Kaza</td><td>${p.kaza || p.properti_4 || '—'}</td></tr>
      <tr><td>Vilayet</td><td>${p.vilayet || p.properti_5 || '—'}</td></tr>
    </table>`;
}

function christianBuildingPopup(feature) {
  const p = feature.properties;
  return `
    <h4>${p.name || 'Christian Building'}</h4>
    <span class="tag" style="background:#55efc422;color:#55efc4;">Christian building</span>
    <table>
      <tr><td>Denomination</td><td>${p.denomination || p.properti_2 || '—'}</td></tr>
      <tr><td>City</td><td>${p.city || p.properti_4 || '—'}</td></tr>
      <tr><td>Country</td><td>${p.country || p.properti_3 || '—'}</td></tr>
    </table>`;
}

function commercialPopup(feature) {
  const p = feature.properties;
  return `
    <h4>Commercial Center</h4>
    <span class="tag" style="background:#ffeaa722;color:#ffeaa7;">Commercial center</span>
    <table>
      <tr><td>ID</td><td>${p.Id || '—'}</td></tr>
    </table>`;
}

// ── Layer builders ────────────────────────────────────────────────────────────

function buildKazaLayer(geojson) {
  return L.geoJSON(geojson, {
    style: kazaStyle,
    onEachFeature: (feature, layer) => {
      layer.bindPopup(() => kazaPopup(feature), { maxWidth: 300 });
      layer.on({
        mouseover(e) {
          e.target.setStyle({ weight: 2, color: '#c8a96e', fillOpacity: 0.85 });
          updateStatsPanel(feature.properties);
        },
        mouseout(e) {
          state.leafletLayers.kazas.resetStyle(e.target);
          clearStatsPanel();
        },
        click(e) { state.map.fitBounds(e.target.getBounds(), { padding: [20,20] }); },
      });
    },
  });
}

function buildPointLayer(geojson, key, popupFn) {
  const style = POINT_STYLES[key];
  return L.geoJSON(geojson, {
    pointToLayer(feature, latlng) {
      return L.circleMarker(latlng, {
        radius: style.radius,
        fillColor: style.color,
        color: '#ffffff',
        weight: 0.8,
        opacity: 0.9,
        fillOpacity: 0.85,
      });
    },
    onEachFeature(feature, layer) {
      layer.bindPopup(() => popupFn(feature), { maxWidth: 300 });
    },
  });
}

// ── Stats panel ───────────────────────────────────────────────────────────────

function updateStatsPanel(p) {
  const el = document.getElementById('stats-panel');
  if (!el) return;
  const fmt  = v => (v != null && !isNaN(v)) ? Number(v).toLocaleString() : '—';
  const pct  = v => (v != null && !isNaN(v)) ? (v * 100).toFixed(1) + '%' : '—';

  el.innerHTML = `
    <b>${p.kaza || p.RTENO || 'Kaza'}</b>
    <div class="stat-row"><span>Grand total</span><span>${fmt(p.GrandTotal)}</span></div>
    <div class="stat-row"><span>Muslims</span>
      <span>${fmt((+p.Muslims_Female || 0) + (+p.Muslims_Male || 0))}</span></div>
    <div class="stat-row"><span>Armenians</span>
      <span>${fmt(p.Total_Armenian)}</span></div>
    <div class="stat-row"><span>Greeks</span>
      <span>${fmt((+p.Greeks_Female || 0) + (+p.Greeks_Male || 0))}</span></div>
    <div class="stat-row"><span>Christian share</span><span>${pct(p.ChristianShare)}</span></div>
    <div class="stat-row"><span>Armenian share</span><span>${pct(p.ArmenianShare)}</span></div>`;
}

function clearStatsPanel() {
  const el = document.getElementById('stats-panel');
  if (el) el.innerHTML = '<span style="color:#606880;font-style:italic;">Hover a kaza to see census data.</span>';
}

// ── Legend ────────────────────────────────────────────────────────────────────

function buildChoroplethLegend() {
  const scaleEl  = document.querySelector('.legend-scale');
  const labelsEl = document.querySelector('.legend-labels');
  if (!scaleEl || !labelsEl) return;

  CHOROPLETH_COLORS.forEach(c => {
    const div = document.createElement('div');
    div.style.cssText = `flex:1;background:${c};`;
    scaleEl.appendChild(div);
  });

  ['0%', '2%', '5%', '10%', '20%', '35%', '100%'].forEach(t => {
    const span = document.createElement('span');
    span.textContent = t;
    labelsEl.appendChild(span);
  });
}

// ── Toggle layer visibility ───────────────────────────────────────────────────

function setLayerVisible(key, visible) {
  const layer = state.leafletLayers[key];
  if (!layer) return;
  if (visible) {
    if (!state.map.hasLayer(layer)) state.map.addLayer(layer);
  } else {
    if (state.map.hasLayer(layer)) state.map.removeLayer(layer);
  }
  state.visible[key] = visible;
}

function bindToggleCheckboxes() {
  document.querySelectorAll('[data-layer]').forEach(cb => {
    cb.addEventListener('change', e => {
      setLayerVisible(e.target.dataset.layer, e.target.checked);
    });
  });
}

// ── Fetch all GeoJSON ─────────────────────────────────────────────────────────

async function fetchAll() {
  const entries = Object.entries(LAYERS_CONFIG);
  const results = await Promise.allSettled(
    entries.map(([, cfg]) =>
      fetch(DATA_BASE + cfg.file).then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}: ${cfg.file}`);
        return r.json();
      })
    )
  );
  const data = {};
  entries.forEach(([key], i) => {
    if (results[i].status === 'fulfilled') {
      data[key] = results[i].value;
    } else {
      console.warn(`Could not load layer "${key}":`, results[i].reason);
    }
  });
  return data;
}

// ── Main ──────────────────────────────────────────────────────────────────────

async function main() {
  initMap();
  buildChoroplethLegend();
  clearStatsPanel();

  let data;
  try {
    data = await fetchAll();
  } catch (err) {
    console.error('Fatal fetch error:', err);
    return;
  }

  // Historical map overlay — added below base tiles, above nothing yet
  state.leafletLayers.ottoman1899 = L.imageOverlay(
    OTTOMAN_OVERLAY.url,
    OTTOMAN_OVERLAY.bounds,
    { opacity: OTTOMAN_OVERLAY.opacity, interactive: false }
  );

  // Build and register layers (order matters for z-stacking)
  if (data.kazas) {
    state.leafletLayers.kazas = buildKazaLayer(data.kazas);
  }
  if (data.armenian) {
    state.leafletLayers.armenian = buildPointLayer(data.armenian, 'armenian', armenianSchoolPopup);
  }
  if (data.christian) {
    state.leafletLayers.christian = buildPointLayer(data.christian, 'christian', christianBuildingPopup);
  }
  if (data.commercial) {
    state.leafletLayers.commercial = buildPointLayer(data.commercial, 'commercial', commercialPopup);
  }
  if (data.locations) {
    state.leafletLayers.locations = buildPointLayer(data.locations, 'locations', locationPopup);
  }
  if (data.mainStations) {
    state.leafletLayers.mainStations = buildPointLayer(data.mainStations, 'mainStations', stationPopup);
  }

  // Add layers according to initial visibility state
  Object.keys(state.leafletLayers).forEach(key => {
    setLayerVisible(key, state.visible[key] ?? false);
  });

  bindToggleCheckboxes();

  // Dismiss loading overlay
  const loading = document.getElementById('loading');
  if (loading) {
    loading.classList.add('hidden');
    setTimeout(() => loading.remove(), 500);
  }
}

document.addEventListener('DOMContentLoaded', main);
