import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from "recharts";

type DataPoint = {
  date: string;
  actual: number | null;
  forecast: number | null;
};

const ForecastChart = () => {
  const [productId, setProductId] = useState(1);
  const [warehouseId, setWarehouseId] = useState(1);
  const [data, setData] = useState<DataPoint[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);

    try {
      const res = await fetch(
        `http://127.0.0.1:8000/forecast/comparison?product_id=${productId}&warehouse_id=${warehouseId}`
      );

      const result = await res.json();

      const map = new Map<string, DataPoint>();

      // 🔵 Actual
      result.actual.dates.forEach((date: string, i: number) => {
        map.set(date, {
          date,
          actual: result.actual.values[i],
          forecast: null
        });
      });

      // 🟣 Forecast (future)
      result.forecast.dates.forEach((date: string, i: number) => {
        if (!map.has(date)) {
          map.set(date, {
            date,
            actual: null,
            forecast: result.forecast.values[i]
          });
        } else {
          map.get(date)!.forecast = result.forecast.values[i];
        }
      });

      const formatted = Array.from(map.values()).sort(
        (a, b) =>
          new Date(a.date).getTime() - new Date(b.date).getTime()
      );

      setData(formatted);
    } catch (err) {
      console.error("Error fetching forecast:", err);
    }

    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, [productId, warehouseId]);

  const lastActualDate =
    data.filter(d => d.actual !== null).slice(-1)[0]?.date;

  return (
    <div className="p-4 bg-white rounded-2xl shadow">
      <h2 className="text-xl font-semibold mb-4">
        Demand Forecast
      </h2>

      {/* 🔽 Filters */}
      <div className="flex gap-4 mb-4">
        <label>Product ID</label>
        <input
          type="number"
          value={productId}
          onChange={(e) => setProductId(Number(e.target.value))}
          className="border px-3 py-2 rounded w-26"
          placeholder="Product ID"
        />
        <label>Warehouse ID</label>
        <input
          type="number"
          value={warehouseId}
          onChange={(e) => setWarehouseId(Number(e.target.value))}
          className="border px-3 py-2 rounded w-26"
          placeholder="Warehouse ID"
        />

        <button
          onClick={fetchData}
          className="bg-blue-600 text-white px-4 py-2 rounded"
        >
          Load
        </button>
      </div>

      {/* 📊 Chart */}
      {loading ? (
        <p>Loading...</p>
      ) : (
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={data}>
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
              name="Actual Demand"
            />

            {/* 🟣 Forecast */}
            <Line
              type="monotone"
              dataKey="forecast"
              stroke="#7c3aed"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              connectNulls
              name="Forecast"
            />

            {/* 🔥 Forecast Start Divider */}
            {lastActualDate && (
              <ReferenceLine
                x={lastActualDate}
                stroke="gray"
                strokeDasharray="3 3"
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};

export default ForecastChart;