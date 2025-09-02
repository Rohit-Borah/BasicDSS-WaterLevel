// import { useEffect, useState } from "react";
// import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine, ResponsiveContainer } from "recharts";
// //import axios from 'axios';

// export default function HydroGraph({ station }) {
//   const [data, setData] = useState([]);

//   useEffect(() => {
//     if (!station) return;
//     fetch(`http://localhost:4000/api/hydrograph?station=${encodeURIComponent(station)}`)
// //    axios.get(`/api/hydrograph?station=${encodeURIComponent(station)}`)
//       .then((r) => r.json())
//       .then(setData)
//       .catch(console.error);
//   }, [station]);

//   if (!station) return null;

//   return (
//     <div style={{ width: "100%", height: 220, marginTop: 10 }}>
//       <ResponsiveContainer>
//         <LineChart data={data}>
//           <CartesianGrid strokeDasharray="3 3" />
//           <XAxis dataKey="date" />
//           <YAxis domain={["auto", "auto"]} />
//           <Tooltip />
//           <Legend />
//           <Line type="monotone" dataKey="morning" stroke="#1f77b4" dot />
//           <Line type="monotone" dataKey="evening" stroke="#ff7f0e" dot />
//           <ReferenceLine y={data[0]?.warning_level} label="Warning" stroke="orange" strokeDasharray="4 4" />
//           <ReferenceLine y={data[0]?.danger_level} label="Danger" stroke="red" strokeDasharray="4 4" />
//           <ReferenceLine y={data[0]?.hfl_m} label="HFL" stroke="purple" strokeDasharray="4 4" />
//         </LineChart>
//       </ResponsiveContainer>
//     </div>
//   );
// }

import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine, ResponsiveContainer
} from 'recharts';

const HydroGraph = ({ station }) => {
  const [data, setData] = useState([]);

  useEffect(() => {
    if (!station) return;
    axios.get(`/api/hydrograph?station=${encodeURIComponent(station)}`)
      .then(res => setData(res.data))
      .catch(err => console.error(err));
  }, [station]);

  if (!station) return <p>Select a station to view hydrograph</p>;

  if (!data.length) return <p>Loading hydrograph...</p>;

  const refLevels = data.length ? {
    warning: data[0].warning,
    danger: data[0].danger,
    hfl: data[0].hfl
  } : {};

  return (
    <div style={{ width: '100%', height: 400 }}>
      <ResponsiveContainer>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="datetime" angle={-30} textAnchor="end" height={70} />
          <YAxis label={{ value: 'Water Level (m)', angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Legend />

          <Line type="monotone" dataKey="level" stroke="#1f77b4" name="Water Level" dot={true} />

          <ReferenceLine y={refLevels.warning} stroke="orange" label="Warning" />
          <ReferenceLine y={refLevels.danger} stroke="red" label="Danger" />
          <ReferenceLine y={refLevels.hfl} stroke="purple" label="HFL" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default HydroGraph;