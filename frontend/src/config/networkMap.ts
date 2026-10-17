
const center: [number, number] = [33.7760948, -84.3988077];
const radiusWithMarginKm = 10.8;
const latitudeDelta = radiusWithMarginKm / 111.32;
const longitudeDelta = radiusWithMarginKm / (111.32 * Math.cos(center[0] * Math.PI / 180));

export const networkMapConfig = {
  center,
  radiusKm: 10,
  zoom: 12,
  minZoom: 10,
  maxZoom: 17,
  maxBounds: [
    [center[0] - latitudeDelta, center[1] - longitudeDelta],
    [center[0] + latitudeDelta, center[1] + longitudeDelta],
  ] as [[number, number], [number, number]],
};
