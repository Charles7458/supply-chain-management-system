import React, { useEffect, useState } from "react";
import { API_ADDRESS } from "../backend";

type Alert = {
  alert_id: number;
  alert_type: string;
  alert_message: string;
  created_at: string;
};

const AlertsList: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);

  useEffect(() => {
    fetch(API_ADDRESS+"/dashboard/alerts")
      .then((res) => res.json())
      .then(setAlerts)
      .catch(console.error);
  }, []);

  return (
    <div className="bg-white p-4 rounded-2xl shadow-md">
      <h2 className="text-lg font-semibold mb-4">Recent Alerts</h2>

      <div className="space-y-2 max-h-64 overflow-y-auto">
        {alerts.map((a) => (
          <div
            key={a.alert_id}
            className="border p-2 rounded-lg text-sm"
          >
            <p className="font-medium">{a.alert_type}</p>
            <p className="text-gray-600">{a.alert_message}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AlertsList;