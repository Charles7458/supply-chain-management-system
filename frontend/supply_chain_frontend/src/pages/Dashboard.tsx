import { useEffect, useState } from "react";
import SummaryCard from "../components/SummaryCards";
import DemandTrendChart from "../components/DemandTrendChart";
import ForecastChart from "../components/ForecastChart";
import AlertsList from "../components/AlertsList";
import RiskInsights from "../components/RiskInsights";
import { API_ADDRESS } from "../backend";

type Summary = {
  total_products: number;
  total_warehouses: number;
  total_alerts: number;
};

const Dashboard: React.FC = () => {
  const [summary, setSummary] = useState<Summary | null>(null);

  const productId = 1;
  const warehouseId = 1;

  useEffect(() => {
    fetch(API_ADDRESS+"/dashboard/summary")
      .then((res) => res.json())
      .then(setSummary)
      .catch(console.error);
  }, []);

  return (
    <div className="p-6 bg-gray-100 min-h-screen">

      {/* 🔹 Title */}
      <h1 className="text-2xl font-bold mb-6">
        Supply Chain Dashboard
      </h1>

      {/* 🔹 Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <SummaryCard
          title="Total Products"
          value={summary?.total_products ?? "-"}
        />
        <SummaryCard
          title="Warehouses"
          value={summary?.total_warehouses ?? "-"}
        />
        <SummaryCard
          title="Active Alerts"
          value={summary?.total_alerts ?? "-"}
        />
      </div>

      {/* 🔹 Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <DemandTrendChart
          productId={productId}
          warehouseId={warehouseId}
        />
        <ForecastChart
          productId={productId}
          warehouseId={warehouseId}
        />
      </div>

      {/* 🔹 Bottom Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 ">
        <AlertsList />

        <RiskInsights />
      </div>

    </div>
  );
};

export default Dashboard;