import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend
} from "recharts";

const ForecastPage = () => {
  const [trendData, setTrendData] = useState<any[]>([]);
  const [comparisonDataLGB, setComparisonDataLGB] = useState<any[]>([]);
  const [comparisonDataRF, setComparisonDataRF] = useState<any[]>([]);
  const [comparisonDataAll, setComparisonDataAll] = useState<any[]>([]);
  const [insights, setInsights] = useState<any>({});

  const [product_id, setProductId] = useState<number>(1);
  const [warehouse_id, setWarehouseId] = useState<number>(1);

  useEffect(() => {
    if(product_id > 0 && warehouse_id > 0){
      fetchTrend();
      fetchComparisonLGB();
      fetchComparisonRF();
      fetchComparisonAll();
    }
  }, [product_id,warehouse_id]);

  const fetchTrend = async () => {
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/forecast/demand-trend?product_id=${product_id}&warehouse_id=${warehouse_id}`
      );

      const data = await res.json();
      setTrendData(data);

    } catch (err) {
      console.error("Error fetching trend:", err);
    }
  };

  const fetchComparisonLGB = async () => {
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/forecast/comparison?product_id=${product_id}&warehouse_id=${warehouse_id}`
      );

      if (!res.ok) throw new Error("API error");

      const data = await res.json();

      // 🔥 Merge actual + forecast into one timeline
      const formatted = [
        ...data.actual.dates.map((date: string, i: number) => ({
          date,
          actual: data.actual.values[i],
          forecast: null
        })),
        ...data.forecast.dates.map((date: string, i: number) => ({
          date,
          actual: null,
          forecast: data.forecast.values[i]
        }))
      ];

      setComparisonDataLGB(formatted);

      // 🔹 Insights (use actual only)
      const avg =
        data.actual.values.reduce((a: number, b: number) => a + b, 0) /
        data.actual.values.length;

      setInsights({
        avgDemand: avg.toFixed(2),
        latestForecast: data.forecast.values.slice(-1)[0]?.toFixed(2)
      });

    } catch (err) {
      console.error("Error fetching comparison:", err);
    }
  };

  const fetchComparisonRF = async () => {
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/forecast/comparison?product_id=${product_id}&warehouse_id=${warehouse_id}&model=rf`
      );

      if (!res.ok) throw new Error("API error");

      const data = await res.json();

      // 🔥 Merge actual + forecast into one timeline
      const formatted = [
        ...data.actual.dates.map((date: string, i: number) => ({
          date,
          actual: data.actual.values[i],
          forecast: null
        })),
        ...data.forecast.dates.map((date: string, i: number) => ({
          date,
          actual: null,
          forecast: data.forecast.values[i]
        }))
      ];

      setComparisonDataRF(formatted);

      // 🔹 Insights (use actual only)
      const avg =
        data.actual.values.reduce((a: number, b: number) => a + b, 0) /
        data.actual.values.length;

      setInsights({
        avgDemand: avg.toFixed(2),
        latestForecast: data.forecast.values.slice(-1)[0]?.toFixed(2)
      });

    } catch (err) {
      console.error("Error fetching comparison:", err);
    }
  };

  const fetchComparisonAll = async () => {
    const res = await fetch(
      `http://127.0.0.1:8000/forecast/compare-all?product_id=1&warehouse_id=1`
    );

    const data = await res.json();

    const map = new Map();

    // 🔵 Actual
    data.actual.dates.forEach((date: string, i: number) => {
      map.set(date, {
        date,
        actual: data.actual.values[i],
        rf: null,
        lgb: null
      });
    });

    // 🟢 RF Forecast
    data.rf.dates.forEach((date: string, i: number) => {
      if (!map.has(date)) {
        map.set(date, { date, actual: null, rf: null, lgb: null });
      }
      map.get(date).rf = data.rf.values[i];
    });

    // 🟣 LGB Forecast
    data.lgb.dates.forEach((date: string, i: number) => {
      if (!map.has(date)) {
        map.set(date, { date, actual: null, rf: null, lgb: null });
      }
      map.get(date).lgb = data.lgb.values[i];
    });

    // 🔥 Convert to sorted array
    const formatted = Array.from(map.values()).sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
    );

    setComparisonDataAll(formatted);
};

  return (
    <div className="p-6 space-y-8">

      {/* Warehouse Filter */}
        <div className="flex gap-x-10">
          <div>
            <p className="font-semibold text-gray-500">Warehouse ID</p>
            <input type="number"
              className="mb-4 p-2 border rounded-lg w-full max-w-sm"
              value={warehouse_id}
              onChange={(e) => {
                  setWarehouseId(parseInt(e.target.value));
              }}
            />
          </div>

        {/* Status Filter */}
          <div>
            <p className="font-semibold text-gray-500">Product ID</p>
            <input type="number"
              className="mb-4 p-2 border rounded-lg w-full max-w-sm"
              value={product_id}
              onChange={e=>{setProductId(parseInt(e.target.value))}}
            />
          </div>
      </div>


      {/* 🔹 Insights */}
      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-white rounded shadow">
          <h3 className="text-gray-500">Avg Demand</h3>
          <p className="text-xl font-bold">{insights.avgDemand}</p>
        </div>

        <div className="p-4 bg-white rounded shadow">
          <h3 className="text-gray-500">Latest Forecast</h3>
          <p className="text-xl font-bold">{insights.latestForecast}</p>
        </div>
      </div>

      {/* 🔥 Demand Trend */}
      <div className="bg-white p-4 rounded shadow">
        <h2 className="text-lg font-semibold mb-4">Demand Trend</h2>

        <LineChart width={800} height={300} data={trendData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="sale_date" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="quantity_sold" />
        </LineChart>
      </div>

      {/* 🔥 Forecast vs Actual */}
      <div className="bg-white p-4 rounded shadow">
        <h2 className="text-lg font-semibold mb-4">Forecast vs Actual (LightGBM)</h2>

        <LineChart width={800} height={300} data={comparisonDataLGB}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />

          {/* Actual */}
          <Line
            type="monotone"
            dataKey="actual"
            stroke="#2563eb"
            strokeWidth={2}
            dot={false}
          />

          {/* Forecast */}
          <Line
            type="monotone"
            dataKey="forecast"
            stroke="#f59e0b"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
          />
        </LineChart>
      </div>

            <div className="bg-white p-4 rounded shadow">
        <h2 className="text-lg font-semibold mb-4">Forecast vs Actual (Random Forest)</h2>

        <LineChart width={800} height={300} data={comparisonDataRF}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />

          {/* Actual */}
          <Line
            type="monotone"
            dataKey="actual"
            stroke="#2563eb"
            strokeWidth={2}
            dot={false}
          />

          {/* Forecast */}
          <Line
            type="monotone"
            dataKey="forecast"
            stroke="#f59e0b"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
          />
        </LineChart>
      </div>

      <div className="bg-white p-4 rounded shadow">
        <h2>Forecast(LGBM) vs Forecast(RF) vs Actual</h2>
        <LineChart width={900} height={350} data={comparisonDataAll}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />

          {/* 🔵 Actual */}
          <Line
            type="monotone"
            dataKey="actual"
            stroke="#2563eb"
            strokeWidth={2}
            dot={false}
          />

          {/* 🟢 Random Forest */}
          <Line
            type="monotone"
            dataKey="rf"
            stroke="#10b981"
            strokeWidth={2}
            strokeDasharray="4 4"
            dot={false}
          />

          {/* 🟣 LightGBM */}
          <Line
            type="monotone"
            dataKey="lgb"
            stroke="#7c3aed"
            strokeWidth={2}
            strokeDasharray="6 6"
            dot={false}
          />

        </LineChart>
      </div>

    </div>
  );
};

export default ForecastPage;