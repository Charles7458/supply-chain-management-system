import { useEffect, useState } from "react";

type Alert = {
  product_id: number;
  product_name: string;
  warehouse_id: number;
  warehouse_name: string;
  available_stock: number;
  status: string;
  message: string;
};

const AlertsPanel = () => {
  const [groupBy, setGroupBy] = useState("none");
  const [data, setData] = useState<any>(null);

  const fetchAlerts = async () => {
    const res = await fetch(
      `http://127.0.0.1:8000/dashboard/alerts?group_by=${groupBy}`
    );
    const result = await res.json();
    console.log(result)
    setData(result);
  };

  useEffect(() => {
    fetchAlerts();
  }, [groupBy]);

  const getColor = (status: string) => {
    if (status === "CRITICAL") return "text-red-600";
    if (status === "REORDER") return "text-orange-500";
    return "text-gray-500";
  };

  return (
    <div className="p-4 bg-white rounded-2xl shadow h-fit">
      <h2 className="text-xl font-semibold mb-4 inline me-10">Alerts</h2>

      {/* 🔽 Group Selector */}
      <select
        value={groupBy}
        onChange={(e) => setGroupBy(e.target.value)}
        className="border px-3 py-2 mb-4 rounded"
      >
        <option value="none">No Grouping</option>
        <option value="warehouse">Group by Warehouse</option>
        <option value="status">Group by Status</option>
      </select>

      {/* 🔥 Render */}
      {data?.group_by === "none" && (
        <div className="space-y-2 overflow-auto h-90">
          {data?.data?.map((alert: Alert, i: number) => (
            <div key={i} className="p-3 border rounded">
              <p className={getColor(alert.status)}>
                {alert.message}
              </p>
              <p className="text-sm text-gray-500">
                {alert.product_name} — {alert.warehouse_name}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* 🔥 GROUPED VIEW */}
      {data?.group_by !== "none" &&
        Object.entries(data?.data || {}).map(([group, alerts]: any) => (
          <div key={group} className="mb-4">
            <h3 className="font-semibold text-lg mb-2">{group}</h3>

            <div className="space-y-2">
              {alerts.map((alert: Alert, i: number) => (
                <div key={i} className="p-3 border rounded">
                  <p className={getColor(alert.status)}>
                    {alert.message}
                  </p>
                  <p className="text-sm text-gray-500">
                    {alert.product_name} — {alert.warehouse_name}
                  </p>
                </div>
              ))}
            </div>
          </div>
        ))}
    </div>
  );
};

export default AlertsPanel;