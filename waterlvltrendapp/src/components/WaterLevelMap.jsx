import { useEffect, useMemo, useRef, useState } from "react";
import Map from "ol/Map";
import View from "ol/View";
import TileLayer from "ol/layer/Tile";
import OSM from "ol/source/OSM";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import { fromLonLat } from "ol/proj";
import { Feature } from "ol";
import Point from "ol/geom/Point";
import { Icon, Style } from "ol/style";
import Overlay from "ol/Overlay";

const iconStyle = new Style({
  image: new Icon({
    //src: "https://cdn.jsdelivr.net/npm/ol@latest/examples/data/icon.png",
    src: "https://cdn-icons-png.flaticon.com/512/684/684908.png",
    scale: 0.05,
    anchor: [0.5, 1],
  }),
});

export default function WaterLevelMap() {
  const mapRef = useRef(null);
  const containerRef = useRef(null);
  const contentRef = useRef(null);
  const closerRef = useRef(null);

  const [dateISO, setDateISO] = useState(() => new Date().toISOString().slice(0, 10));
  const [session, setSession] = useState("Morning");
  const [featuresData, setFeaturesData] = useState([]);

  const vectorSource = useMemo(() => new VectorSource(), []);
  const vectorLayer = useMemo(() => new VectorLayer({ source: vectorSource }), [vectorSource]);

  useEffect(() => {
    const map = new Map({
      target: mapRef.current,
      layers: [
        new TileLayer({ source: new OSM() }),
        vectorLayer,
      ],
      view: new View({
        center: fromLonLat([92.5, 26.2]),
        zoom: 6,
      }),
    });

    const overlay = new Overlay({
      element: containerRef.current,
      autoPan: { animation: { duration: 250 } },
    });
    map.addOverlay(overlay);

    closerRef.current.onclick = function () {
      overlay.setPosition(undefined);
      closerRef.current.blur();
      return false;
    };

    map.on("singleclick", (evt) => {
      const feature = map.forEachFeatureAtPixel(evt.pixel, (f) => f);
      if (feature) {
        const props = feature.getProperties();
        const geom = feature.getGeometry();
        const coord = geom.getCoordinates();
        const p = props._popupProps;
        contentRef.current.innerHTML = `
          <div style="font-family: system-ui; font-size: 14px; line-height:1.2">
            <div style="font-weight:700; margin-bottom:4px">${p.station} (${p.river})</div>
            <div><b>Warning:</b> ${p.warning_level ?? "-"} m</div>
            <div><b>Danger:</b> ${p.danger_level ?? "-"} m</div>
            <div><b>HFL:</b> ${p.hfl_m ?? "-"} m</div>
            <div><b>Water @ ${p.time_label}:</b> ${p.water_level_m ?? "-"} m</div>
            <div><b>Trend:</b> ${p.trend ?? "-"}</div>
            <div style="margin-top:4px; color:#666">${p.district || ""}</div>
          </div>`;
        overlay.setPosition(coord);
      }
    });

    return () => map.setTarget(undefined);
  }, [vectorLayer]);

  useEffect(() => {
    const url = new URL("/api/stations", "http://localhost:4000");
    url.searchParams.set("date", dateISO);
    url.searchParams.set("session", session);

    fetch(url.toString())
      .then((r) => r.json())
      .then((geojson) => setFeaturesData(geojson.features || []))
      .catch((e) => console.error(e));
  }, [dateISO, session]);

  useEffect(() => {
    vectorSource.clear();
    const feats = featuresData.map((f) => {
      const [lon, lat] = f.geometry.coordinates;
      const feature = new Feature({
        geometry: new Point(fromLonLat([lon, lat])),
        _popupProps: {
          river: f.properties.river,
          station: f.properties.station,
          district: f.properties.district,
          warning_level: f.properties.warning_level,
          danger_level: f.properties.danger_level,
          hfl_m: f.properties.hfl_m,
          water_level_m: f.properties.water_level_m,
          trend: f.properties.trend,
          time_label: f.properties.time_label,
        },
      });
      feature.setStyle(iconStyle);
      return feature;
    });
    vectorSource.addFeatures(feats);
  }, [featuresData, vectorSource]);

  return (
    <div style={{ display: "grid", gridTemplateRows: "auto 1fr", height: "100vh" }}>
      <div style={{ padding: 8, display: "flex", gap: 8, alignItems: "center", fontFamily: "system-ui" }}>
        <label>
          Date:
          <input type="date" value={dateISO} onChange={(e) => setDateISO(e.target.value)} />
        </label>
        <label>
          Session:
          <select value={session} onChange={(e) => setSession(e.target.value)}>
            <option>Morning</option>
            <option>Evening</option>
          </select>
        </label>
      </div>

      <div ref={mapRef} style={{ width: "100%", height: "100%" }} />

      <div ref={containerRef} className="ol-popup" style={{ position: "absolute", background: "white", padding: 8, borderRadius: 8, boxShadow: "0 6px 24px rgba(0,0,0,0.2)", border: "1px solid #ddd", bottom: 12, left: 12, minWidth: 220 }}>
        <a ref={closerRef} href="#" style={{ position: "absolute", top: 4, right: 6, textDecoration: "none" }}>✕</a>
        <div ref={contentRef}></div>
      </div>
    </div>
  );
}