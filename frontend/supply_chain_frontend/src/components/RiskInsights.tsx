import { useEffect, useState } from "react";

type Insight = {
  product_name: string;
  warehouse_name: string;
  available_stock: number;
  risk_level: string;
  risk_score: number;
  action: string;
};

const RiskInsights = () => {
  const [data, setData] = useState<Insight[]>([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/dashboard/risk-insights")
      .then(res => res.json())
      .then(res => setData(res.data));
  }, []);

  const getColor = (level: string) => {
    if (level === "HIGH") return "text-red-600";
    if (level === "MEDIUM") return "text-orange-500";
    return "text-green-600";
  };

  return (
    <div className="p-4 bg-white rounded-2xl shadow h-fit">
      <h2 className="text-xl font-semibold mb-7">Risk Insights</h2>

      <div className="space-y-2 overflow-auto h-90">
        {data.map((item, i) => (
          <div key={i} className="p-3 border rounded">
            <p className={getColor(item.risk_level)}>
              {item.product_name} ({item.warehouse_name})
            </p>

            <p className="text-sm">
              Available: {item.available_stock} | Risk Score: {item.risk_score}
            </p>

            <p className="text-sm text-gray-500">{item.action}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RiskInsights;