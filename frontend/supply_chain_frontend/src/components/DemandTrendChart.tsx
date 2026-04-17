import React, { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";

import { API_ADDRESS } from "../backend";


type DemandData = {
  date: string;
  demand: number;
};

type Props = {
  productId: number;
  warehouseId: number;
};

const DemandTrendChart: React.FC<Props> = ({ productId, warehouseId }) => {
  const [data, setData] = useState<DemandData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(
          API_ADDRESS+`/dashboard/demand-trend?product_id=${productId}&warehouse_id=${warehouseId}&days=30`
        );
        const json = await res.json();
        setData(json);
      } catch (error) {
        console.error("Error fetching demand trend:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [productId, warehouseId]);

  if (loading) {
    return <div>Loading demand trend...</div>;
  }

  if (!data.length) {
    return <div>No data available</div>;
  }

  return (
    <div className="bg-white p-4 rounded-2xl shadow-md">
      <h2 className="text-lg font-semibold mb-4">Demand Trend</h2>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />

          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
          />

          <YAxis />

          <Tooltip />

          <Line
            type="monotone"
            dataKey="demand"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default DemandTrendChart;