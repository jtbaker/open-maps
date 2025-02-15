<script setup lang="ts">
// import HelloWorld from './components/HelloWorld.vue'
import LayerControl from "./components/LayerControl.vue";
import "maplibre-gl/dist/maplibre-gl.css";
import { ref, onMounted, watchEffect } from "vue";
import {
  Map,
  Popup,
  FullscreenControl,
  NavigationControl,
  ScaleControl,
  GlobeControl,
  GeolocateControl,
} from "maplibre-gl";
import { scaleQuantize, scaleSequential, scaleQuantile, scaleLinear, scaleOrdinal } from "d3-scale";
const hoverFeature = ref<Record<string, any>>({});
const hoverFeatureId = ref<number | string | undefined>(undefined);

const mapRef = ref<HTMLDivElement | null>(null);
const popupRef = ref<HTMLDivElement | null>(null);
let map: Map | null = null;
let popup: Popup | null = null;
let rasterSaturation = ref<number>(0.0);
const mapIsLoaded = ref<boolean>(false)

const scale = scaleOrdinal<number, string>()
  .domain([0,
    500000,
    1000000,
    2000000,
    3000000,
    4000000,
    5000000,
    10000000,
    100000000,
  ]).range(["#C4A484",
    "#8B8B5A",
    "#567D46",
    "#4B7BE5",
    "#3266D1",
    "#1E4CB5",
    "#163C91",
    "#0F2D6D",
    "#081D49",
  ])
onMounted(() => {
  popup = new Popup({
    anchor: "top",
    maxWidth: '300px'
  })

  map = new Map({
    container: mapRef.value as HTMLDivElement,
    hash: true,
    center: [-74.006, 40.7128],
    zoom: 9,
    style: {
      version: 8,
      glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
      sources: {
        topography: {
          type: "vector",
          tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.pbf"],
        },
        zcta: {
          type: "vector",
          promoteId: "zip_code",
          url: "http://localhost:8000/zcta/tilejson.json",
        },
        satellite: {
          type: "raster",
          tiles: [
            "https://server.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
          ],
          tileSize: 256
        },
        cartoPositron: {
          type: "raster",
          tiles: [
            "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
            "https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
            "https://c.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png"
          ]
        }
      },
      layers: [
        {
          id: "satellite",
          source: "satellite",
          type: "raster",
          paint: {
            "raster-saturation": rasterSaturation.value,
          },
          layout: {
            "visibility": "visible"
          }
        },
        {
          id: "carto-positron",
          source: "cartoPositron",
          type: "raster",
          layout: {
            visibility: "visible"
          }
        },
        {
          id: "zcta",
          source: "zcta",
          "source-layer": "zcta",
          type: "fill",
          paint: {
            "fill-color": [
              "interpolate",
              ["linear"],
              ["coalesce", ["get", "area_water_meters"], 0],
              0,
              "#C4A484", // Light brown/tan (dry earth)
              500000,
              "#8B8B5A", // Olive brown (semi-arid)
              1000000,
              "#567D46", // Muted green (light vegetation)
              2000000,
              "#4B7BE5", // Light blue (some water)
              3000000,
              "#3266D1", // Medium blue
              4000000,
              "#1E4CB5", // Deeper blue
              5000000,
              "#163C91", // Rich blue
              10000000,
              "#0F2D6D", // Dark blue
              100000000,
              "#081D49", // Very dark blue (abundant water)
            ],
            "fill-opacity": [
              "case",
              ["boolean", ["feature-state", "hover"], false],
              0.8,
              0.4,
            ],
          },
        },
        {
          id: "zcta-line",
          source: "zcta",
          "source-layer": "zcta",
          type: "line",
          paint: {
            // "line-color": "#007bff",
            "line-color": [
              "case",
              ["boolean", ["feature-state", "hover"], false],
              "darkgrey",
              "#007bff",
            ],
            "line-width": [
              "interpolate",
              ["exponential", 1],
              ["zoom"],
              5,
              ["case", ["boolean", ["feature-state", "hover"], false], 4, 0.5],
              12,
              ["case", ["boolean", ["feature-state", "hover"], false], 10, 3],
            ],
            "line-opacity": [
              "case",
              ["boolean", ["feature-state", "hover"], false],
              1,
              0.5,
            ],
          },
        },
        {
          id: "zcta-label",
          type: "symbol",
          source: "zcta",
          minzoom: 8,
          "source-layer": "zcta",
          layout: {
            "text-field": "{zip_code}",
            "text-font": ["Open Sans Semibold"],
            "text-size": ["interpolate", ["linear"], ["zoom"], 5, 12, 14, 20],
            "text-anchor": "center",
            "text-allow-overlap": false,
          },
        },
      ],
    },
  });
  map.addControl(new NavigationControl({ showCompass: true }), "top-right");
  map.addControl(new ScaleControl({ unit: "imperial" }), "bottom-left");
  map.addControl(new FullscreenControl(), "top-left");
  map.addControl(new GeolocateControl({}), "top-right");
  map.addControl(new GlobeControl(), "top-right");
  map.on("load", () => {
    map?.setProjection({ type: "globe" });
  });

  map.on("style.load", () => {
    mapIsLoaded.value = true
  })

  watchEffect(() => {
    console.log("firing", rasterSaturation.value);
    if (!map?.isStyleLoaded()) return;
    map?.setPaintProperty(
      "satellite",
      "raster-saturation",
      rasterSaturation.value
    );
  });

  // map.set

  map.on("mousemove", "zcta", (e) => {
    map.getCanvas().style.cursor = "pointer";
    const feature = e.features[0];
    const { properties, id } = feature;
    console.log(properties);
    if (id != hoverFeatureId.value) {
      map?.removeFeatureState({ source: "zcta", sourceLayer: "zcta" });
    }
    hoverFeatureId.value = id;

    console.log({ hoverFeatureId: id });
    map?.setFeatureState(
      { source: "zcta", sourceLayer: "zcta", id: hoverFeatureId.value },
      { hover: true }
    );

    hoverFeature.value = properties;
  });

  map.on("mouseleave", "zcta", () => {
    hoverFeature.value = {}
    hoverFeatureId.value = undefined
    map?.removeFeatureState({ source: "zcta", sourceLayer: "zcta" });
  });


  map.on("click", "zcta", (e) => {
    // map.getCanvas().style.cursor = "pointer";
    popup?.setLngLat(e.lngLat);
    const feature = e.features[0];
    const { properties, id } = feature;
    console.log(properties);
    hoverFeatureId.value = id;
    popup?.setHTML(`<div><span>Postal Code: </span><span>${properties.zip_code}</span></div>`)
    popup?.addTo(map)
  })


});
</script>

<template>
  <div class="h-full w-full flex flex-col items-center justify-around align-middle bg-cyan-800">
    <div>
      <h1 class="text-white text-2xl">Map Viewer</h1>
    </div>
    <div class="h-3/4 w-3/4 flex">
      <div class="w-3/4 p-4 rounded-sm shadow-sm" ref="mapRef"></div>

      <div class="w-3xl bg-opacity-20 p-4 text-white rounded-md shadow-md flex flex-col items-center overflow-auto"
        ref="popupRef">
        <div class="flex w-full items-center content-around justify-evenly">
          <LayerControl v-if="mapIsLoaded" :map="map"></LayerControl>
          <div class="flex flex-col content-around">
            <h3>Legend</h3>
            <div class="flex space-x-2" v-for="d in scale.domain()" :key="d">
              <div class="w-6 h-6 space-y-2 rounded-sm shadow-sm border" :style="{ backgroundColor: scale(d) }"></div>
              <div>{{ d.toLocaleString() }}</div>
            </div>
          </div>
        </div>
        <h4 v-if="Object.keys(hoverFeature).length" class="p-4">
          Feature Details
        </h4>
        <div class="grid grid-cols-2 gap-2">
          <div class="contents" v-for="(value, key) in hoverFeature" :key="key">
            <template v-if="!key.startsWith('internal')">
              <div class="rounded-sm w-sm shadow-sm p-2 font-bold break-words overflow-wrap-break-word truncate">
                {{
                  key
                    .split("_")
                    .map((v) => v.toUpperCase())
                    .join(" ")
                }}
              </div>
              <div class="rounded-sm shadow-sm p-2 break-words overflow-wrap-break-word w-sm">
                {{ value }}
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>
    <div class="flex text-white justify-between content-center items-center place-items-center w-120 p-4">
      <label>Satellite Saturation</label>

      <input v-model.number="rasterSaturation" type="range" min="-1" max="1" step="0.1" />
      <code class="bg-white w-12 h-12 flex items-center justify-center text-gray-600 rounded-sm p-4">
    {{ rasterSaturation }}
  </code>
    </div>
  </div>
</template>
<style></style>
