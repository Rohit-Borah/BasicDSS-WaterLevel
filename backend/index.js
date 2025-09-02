import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import pkg from "pg";

dotenv.config();
const { Pool } = pkg;

const app = express();
app.use(express.json());
app.use(
  cors({
    origin: process.env.CORS_ORIGIN?.split(",") || "*",
  })
);

const pool = new Pool({
  host: process.env.PGHOST,
  port: process.env.PGPORT,
  database: process.env.PGDATABASE,
  user: process.env.PGUSER,
  password: process.env.PGPASSWORD,
});

// Utility: build WHERE clause for date+session, using unique_id and source_file patterns
function buildDateSessionWhere(dateISO, session) {
  if (!dateISO || !session) return { clause: "", params: [] };
  const [yyyy, mm, dd] = dateISO.split("-");
  const dateDot = `${dd}.${mm}.${yyyy}`;

  const clause = `(
      wlb.unique_id ILIKE $1
      OR wlb.source_file ILIKE $2
    )`;
  const params = [
    `%_${dateDot}_${session}%`,
    `%${dateDot}%${session}%`,
  ];
  return { clause, params };
}

// GET /api/stations?date=YYYY-MM-DD&session=Morning|Evening
app.get("/api/stations", async (req, res) => {
  try {
    const { date: dateISO, session } = req.query;
    const { clause, params } = buildDateSessionWhere(dateISO, session);
    const wlExpr = session === "Evening" ? "wlb.water_level_1800hrs_m" : "wlb.water_level_0800hrs_m";

    const whereParts = [];
    const values = [];

    if (clause) {
      whereParts.push(clause);
      values.push(...params);
    }

    whereParts.push("loc.lat IS NOT NULL AND loc.lon IS NOT NULL");

    const whereSQL = whereParts.length ? `WHERE ${whereParts.join(" AND ")}` : "";

    const sql = `
      SELECT
        loc.lon AS longitude,
        loc.lat AS latitude,
        wlb.river,
        wlb.station,
        wlb.district,
        wlb.warning_level_m,
        wlb.danger_level_m,
        wlb.hfl_m,
        ${wlExpr} AS water_level_m,
        wlb.trend,
        wlb.unique_id,
        wlb.source_file
      FROM river_levels_bulletin wlb
      JOIN cwc_location loc
        ON (wlb.river = loc.river AND wlb.station = loc.station)
      ${whereSQL}
      ORDER BY wlb.river, wlb.station;
    `;

    const { rows } = await pool.query(sql, values);

    const features = rows.map((r) => ({
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [Number(r.longitude), Number(r.latitude)],
      },
      properties: {
        river: r.river,
        station: r.station,
        district: r.district,
        warning_level: Number(r.warning_level_m),
        danger_level: Number(r.danger_level_m),
        hfl_m: Number(r.hfl_m),
        water_level_m: r.water_level_m != null ? Number(r.water_level_m) : null,
        trend: r.trend,
        unique_id: r.unique_id,
        source_file: r.source_file,
        session: session === "Evening" ? "Evening" : "Morning",
        time_label: session === "Evening" ? "18:00" : "08:00",
      },
    }));

    res.json({ type: "FeatureCollection", features });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Internal server error" });
  }
});

app.get("/api/health", (req, res) => {
  res.json({ ok: true });
});

const port = process.env.PORT || 4000;
app.listen(port, () => {
  console.log(`API listening on http://localhost:${port}`);
});

//-----------------------------------------------------------------------------------------------------------------------------------------------------------
app.get("/api/hydrograph", async (req, res) => {
  const { station } = req.query;
  if (!station) return res.status(400).json({ error: 'station is required' });

  try {
    const q = `
      SELECT 
        unique_id, source_file,
        warning_level_m, danger_level_m, hfl_m,
        water_level_0800hrs_m, water_level_1800hrs_m
      FROM river_levels_bulletin
      WHERE station = $1
      ORDER BY forecast_date ASC, forecast_time ASC;
    `;
    const { rows } = await pool.query(q, [station]);

    // Transform rows into time-series points
    let data = [];
    rows.forEach(r => {
      if (r.water_level_0800hrs_m !== null) {
        data.push({
          datetime: `${r.forecast_date} 08:00`,
          level: parseFloat(r.water_level_0800hrs_m),
          warning: parseFloat(r.warning_level_m),
          danger: parseFloat(r.danger_level_m),
          hfl: parseFloat(r.hfl_m)
        });
      }
      if (r.water_level_1800hrs_m !== null) {
        data.push({
          datetime: `${r.forecast_date} 18:00`,
          level: parseFloat(r.water_level_1800hrs_m),
          warning: parseFloat(r.warning_level_m),
          danger: parseFloat(r.danger_level_m),
          hfl: parseFloat(r.hfl_m)
        });
      }
    });

    res.json(data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'internal error' });
  }
});

app.listen(5000, () => console.log('API running on http://localhost:5000'));