import 'leaflet';

// 1. Initialize the Map (Zoomed out for world view, center 0,0)
const map = L.map('bloom-map').setView([0, 0], 2); 

// 2. Use a Dark Basemap Tile Layer (Visually Appealing)
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="https://carto.com/attributions">CARTO</a>',
    maxZoom: 18,
}).addTo(map);

// --- 3. Data Styling and Logic (Bloom Intensity using Colors) ---

// Map Chlorophyll-a (simulated by 'intensity') to a color
function getColor(intensity) {
    return intensity > 100 ? '#ff0000' : // High Bloom (Red)
           intensity > 50  ? '#ffcc00' : // Medium Bloom (Yellow)
                             '#6dff6d';  // Low Bloom (Light Green)
}

// Function to style the GeoJSON features
function styleFeature(feature) {
    return {
        radius: 8, // Set marker size
        fillColor: getColor(feature.properties.intensity),
        color: "#fff",
        weight: 1,
        opacity: 1,
        fillOpacity: 0.8
    };
}

// Function to create Circle Markers instead of default icons
function pointToLayer(feature, latlng) {
    return L.circleMarker(latlng, styleFeature(feature));
}

// Function to handle click events and show details (Goal: Clickable Details)
function onEachFeature(feature, layer) {
    if (feature.properties) {
        const props = feature.properties;
        const popupContent = `
            <h3>Bloom Event Details 🌱</h3>
            <strong>Intensity:</strong> <span style="color:${getColor(props.intensity)}; font-weight:bold;">${props.intensity} mg/m³</span>
            <br><strong>Type of Bloom:</strong> ${props.type}
            <br><strong>Detection Date:</strong> ${props.date}
            <br><strong>Satellite Source:</strong> ${props.source}
        `;
        layer.bindPopup(popupContent);
    }
}

// --- 4. Load Data and Add to Map ---
fetch('/data/nasa-blooms.json') // This is the placeholder for your NASA data
    .then(response => response.json())
    .then(data => {
        L.geoJSON(data, {
            pointToLayer: pointToLayer, // Use custom circle markers
            onEachFeature: onEachFeature
        }).addTo(map);

        console.log("Bloom data loaded and rendered.");
    })
    .catch(error => console.error('Error loading bloom data:', error));

// 5. Update Legend (For the sidebar component)
document.getElementById('legend').innerHTML += `
    <div style="display: flex; align-items: center; margin-top: 10px;">
        <span class="intensity-marker high"></span> High (>100 mg/m³)
    </div>
    <div style="display: flex; align-items: center;">
        <span class="intensity-marker medium"></span> Medium (>50 mg/m³)
    </div>
    <div style="display: flex; align-items: center;">
        <span class="intensity-marker low"></span> Low (<50 mg/m³)
    </div>
`;

// Add NASA GIBS Chlorophyll-a WMS Layer for near real-time visualization.
// This provides the colorful, real-time intensity overlay.
const GIBS_CHL_LAYER = L.tileLayer.wms('https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi', {
    layers: 'MODIS_Aqua_Chlorophyll_A', // This is the Chlorophyll-a product layer
    format: 'image/png',
    transparent: true,
    attribution: 'NASA GIBS (Chlorophyll-a)',
    opacity: 0.8,
    // Ensure the data is recent (daily data)
    //time: new Date().toISOString().split('T')[0] 
}).addTo(map);