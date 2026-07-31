import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import { useEffect } from "react";
import type { UiBusiness } from "../../api/types";
import L from "leaflet";

const defaultIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

function FitBounds({ points }: { points: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (!points.length) return;
    if (points.length === 1) {
      map.setView(points[0], 14);
      return;
    }
    map.fitBounds(points, { padding: [40, 40] });
  }, [map, points]);
  return null;
}

export default function ResultsMap({
  items,
  compact = false,
}: {
  items: UiBusiness[];
  /** Shorter map for detail sidebar (h-48). */
  compact?: boolean;
}) {
  const points = items
    .filter((b) => b.latitude != null && b.longitude != null)
    .map((b) => [b.latitude!, b.longitude!] as [number, number]);

  const minH = compact ? "min-h-[12rem]" : "min-h-[320px]";
  const wrapMin = compact ? "min-h-[12rem]" : "min-h-[320px]";
  const emptyMin = compact ? "min-h-[12rem]" : "min-h-[280px]";

  if (!points.length) {
    return (
      <div
        className={`h-full ${emptyMin} rounded-2xl bg-surface-container flex items-center justify-center text-on-surface-variant text-sm p-6 text-center`}
      >
        No map coordinates in these results. List view still works.
      </div>
    );
  }

  return (
    <div
      className={`h-full ${wrapMin} ${
        compact ? "rounded-none border-0" : "rounded-2xl border border-outline-variant/40"
      } overflow-hidden`}
    >
      <MapContainer
        center={points[0]}
        zoom={compact ? 14 : 12}
        scrollWheelZoom={!compact}
        className={`h-full ${minH}`}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FitBounds points={points} />
        {items.map((b) =>
          b.latitude != null && b.longitude != null ? (
            <Marker key={b.id} position={[b.latitude, b.longitude]} icon={defaultIcon}>
              <Popup>
                <strong>{b.title}</strong>
                {b.categories ? <div>{b.categories}</div> : null}
              </Popup>
            </Marker>
          ) : null
        )}
      </MapContainer>
    </div>
  );
}
