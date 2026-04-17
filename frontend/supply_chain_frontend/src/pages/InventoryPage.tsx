import React, { useEffect, useState } from "react";

type InventoryItem = {
  product_id: number;
  product_name: string;
  warehouse_id: number;
  warehouse_name: string;
  stock_level: number;
  reserved_stock: number;
  available_stock: number;
  status: "NORMAL" | "REORDER" | "CRITICAL";
};

const InventoryPage: React.FC = () => {
  const [data, setData] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(false);

  const [warehouseId, setWarehouseId] = useState("");
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [limit] = useState(10);
  const [total, setTotal] = useState(0);

  const [sortBy, setSortBy] = useState("product_name");
  const [order, setOrder] = useState<"asc" | "desc">("asc");

  // 🔥 Fetch API
  const fetchInventory = async () => {
    setLoading(true);

    const params = new URLSearchParams({
      page: String(page),
      limit: String(limit),
      sort_by: sortBy,
      order: order
    });

    if (search) params.append("search", search);
    if (warehouseId) params.append("warehouse_id", warehouseId);
    if (status) params.append("status", status);

    const res = await fetch(`http://127.0.0.1:8000/inventory?${params}`);
    const json = await res.json();

    setData(json.data);
    setTotal(json.total);
    setLoading(false);
  };

  useEffect(() => {
    fetchInventory();
  }, [page, sortBy, order, search, warehouseId, status]);

  // 🔹 Sorting handler
  const handleSort = (column: string) => {
    if (sortBy === column) {
      setOrder(order === "asc" ? "desc" : "asc");
    } else {
      setSortBy(column);
      setOrder("asc");
    }
  };

  const totalPages = Math.ceil(total / limit);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "CRITICAL":
        return "bg-red-100 text-red-600";
      case "REORDER":
        return "bg-yellow-100 text-yellow-600";
      default:
        return "bg-green-100 text-green-600";
    }
  };
  

  async function handlePolicy(){
    const res = await fetch("http://127.0.0.1:8000/policies/generate", {
      method: 'POST'
    })
    const json = await res.json()
    console.log(json.message)
  }

  return (
    <div className="p-6 bg-gray-100 min-h-screen">

      {/* 🔹 Title */}
      <h1 className="text-2xl font-bold mb-4">Inventory</h1>

      {/* 🔹 Search */}
      <input
        type="text"
        placeholder="Search product or warehouse..."
        className="mb-4 p-2 border rounded-lg w-full max-w-sm"
        value={search}
        onChange={(e) => {
          setPage(1);
          setSearch(e.target.value);
        }}
      />

      <div className="flex gap-4 mb-4">

      {/* Warehouse Filter */}
      <select
        className="p-2 border rounded-lg hover:bg-black hover:text-white hover:cursor-pointer"
        value={warehouseId}
        onChange={(e) => {
          setPage(1);
          setWarehouseId(e.target.value);
        }}
      >
        <option value="">All Warehouses</option>
        <option value="1">Warehouse 1</option>
        <option value="2">Warehouse 2</option>
        <option value="3">Warehouse 3</option>
        <option value="4">Warehouse 4</option>
      </select>

      {/* Status Filter */}
      <select
        className="p-2 border rounded-lg hover:bg-black hover:text-white hover:cursor-pointer"
        value={status}
        onChange={(e) => {
          setPage(1);
          setStatus(e.target.value);
        }}
      >
        <option value="">All Status</option>
        <option value="NORMAL">Normal</option>
        <option value="REORDER">Reorder</option>
        <option value="CRITICAL">Critical</option>
      </select>

      <button onClick={handlePolicy} className="bg-sky-500 rounded px-6 hover:cursor-pointer hover:bg-sky-600">Generate Policies</button>
    </div>
      {/* 🔹 Table */}
      <div className="bg-white rounded-2xl shadow-md overflow-x-auto">
        <table className="w-full text-left">

          <thead className="bg-gray-200 text-sm">
            <tr>
              <th className="p-3 cursor-pointer" onClick={() => handleSort("product_name")} title="Sort by Products">
                Product
              </th>
              <th className="p-3 cursor-pointer" onClick={() => handleSort("warehouse_name")} title="Sort by Warehouses">
                Warehouse
              </th>
              <th className="p-3 cursor-pointer" onClick={() => handleSort("stock_level")} title="Sort by Stock level">
                Stock
              </th>
              <th className="p-3">Reserved</th>
              <th className="p-3">Available</th>
              <th className="p-3">Status</th>
            </tr>
          </thead>

          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="p-4 text-center">Loading...</td>
              </tr>
            ) : (
              data.map((item, index) => (
                <tr key={index} className="border-t hover:bg-gray-50">
                  <td className="p-3">{item.product_name}</td>
                  <td className="p-3">{item.warehouse_name}</td>
                  <td className="p-3">{item.stock_level}</td>
                  <td className="p-3">{item.reserved_stock}</td>
                  <td className="p-3">{item.available_stock}</td>

                  <td className="p-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}>
                      {item.status}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>

        </table>
      </div>

      {/* 🔹 Pagination */}
      <div className="flex justify-between items-center mt-4">

        <button
          className="px-4 py-2 bg-gray-300 rounded"
          disabled={page === 1}
          onClick={() => setPage(page - 1)}
        >
          Prev
        </button>

        <span>
          Page {page} of {totalPages}
        </span>

        <button
          className="px-4 py-2 bg-gray-300 rounded"
          disabled={page === totalPages}
          onClick={() => setPage(page + 1)}
        >
          Next
        </button>

      </div>
    </div>
  );
};

export default InventoryPage;