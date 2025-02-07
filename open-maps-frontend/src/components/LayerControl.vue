<template>
    <div class="layer-control text-black bg-white rounded-lg shadow p-4 max-w-xs">
        <h3 class="text-lg font-semibold mb-4">Layers</h3>
        <div class="space-y-2">
            <div>
                <div v-for="layer in layers.filter(v => v.type === 'raster')">
                    <label class="cursor-pointer">
                        <input :value="layer.id" v-model="selectedBaseMapLayerId" type="radio" :id="layer.id"
                            @click="() => { if (selectedBaseMapLayerId != layer.id) { toggleLayer(selectedBaseMapLayerId) }; toggleLayer(layer.id) }">
                        {{ layer.name }}
                    </label>
                </div>
            </div>
            <div v-for="layer in layers.filter(v => v.type !== 'raster')" :key="layer.id" class="flex items-center">
                <input type="checkbox" :id="layer.id" :checked="layer.visible" @change="toggleLayer(layer.id)"
                    class="mr-2" />
                <label :for="layer.id" class="cursor-pointer">
                    {{ layer.name }}
                </label>
                <div v-if="layer.color && layer.type == 'polygon'" class="ml-auto w-8 h-8 rounded"
                    :style="{ backgroundColor: layer.color }" />
                <div v-if="layer.color && layer.type == 'line'" class="ml-auto w-8 h-8 rounded">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-full w-full" viewBox="0 0 100 20">
                        <!-- Background rect for visualization -->
                        <rect width="100" height="20" fill="transparent" />

                        <!-- Curved line using path with bezier curve -->
                        <path d="M 10 10 C 30 -5, 70 25, 90 10" fill="none" stroke="blue" stroke-width="20"
                            stroke-linecap="round" />

                        <!-- Optional dashed curved line (hidden by default) -->
                        <path d="M 10 10 C 30 -5, 70 25, 90 10" fill="none" stroke="blue" stroke-width="20"
                            stroke-dasharray="4 2" stroke-linecap="round" opacity="0" />
                    </svg>
                </div>
                <div v-if="layer.color && layer.type == 'point'" class="ml-auto w-4 h-4 rounded"
                    :style="{ backgroundColor: layer.color }" </div>
                </div>
            </div>
        </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'

import { type LayerSpecification } from "maplibre-gl"
const props = defineProps({
    map: {
        type: Object,
        required: true
    }
})

type LayerType = "polygon" | "line" | "point" | "raster"

interface LayerControlLayer {
    id: string,
    name: string,
    visible: boolean,
    color?: string,
    type: LayerType
}

const layers = ref<LayerControlLayer[]>([])

const selectedBaseMapLayerId = ref<string>("carto-positron")

const formatLayerName = (id: string) => {
    return id
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ').toUpperCase()
}

const getLayerColor = (layer: LayerSpecification) => {
    if (layer.paint) {
        const paintProps = layer.paint
        return (
            paintProps['fill-color'] ||
            paintProps['line-color'] ||
            paintProps['circle-color'] ||
            null
        )
    }
    return null
}

const getLayerType = (layer: LayerSpecification): LayerType | null => {
    if (layer.type === "fill") {
        return "polygon"
    } else if (layer.type === "line") {
        return "line"
    } else if (layer.type === "circle") {
        return "point"
    } else if (layer.type === "raster") {
        return "raster"
    } else {
        return null
    }
}

const initializeLayers = () => {
    // debugger
    // if (!props.map || !props.map.isStyleLoaded()) return

    const mapLayers = props.map.getStyle().layers

    layers.value = mapLayers
        .filter((layer: LayerSpecification) => {
            // Filter out base layers and labels - adjust as needed
            return !layer.id.includes('background') &&
                !layer.id.includes('label')
        })
        .map((layer: LayerSpecification) => ({
            id: layer.id,
            name: formatLayerName(layer.id),
            visible: props.map.getLayoutProperty(layer.id, 'visibility') !== 'none',
            color: getLayerColor(layer),
            type: getLayerType(layer),
        }))
}

const toggleLayer = (layerId: string) => {
    const layer = layers.value.find(l => l.id === layerId)
    if (!layer) return

    const newVisibility = !layer.visible
    layer.visible = newVisibility

    props.map.setLayoutProperty(
        layerId,
        'visibility',
        newVisibility ? 'visible' : 'none'
    )
}

onMounted(() => {
    initializeLayers()
    // props.map.on('styledata', initializeLayers)
})

onBeforeUnmount(() => {
    props.map.off('styledata', initializeLayers)
})
</script>