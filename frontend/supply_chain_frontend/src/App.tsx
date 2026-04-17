import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/NavBar";

// Pages
import Dashboard from "./pages/Dashboard";
import InventoryPage from "./pages/InventoryPage";
import ForecastPage from "./pages/ForecastPage";

function App() {
  return (
    <Router>

      {/* 🔥 Navbar always visible */}
      <Navbar />

      {/* 🔹 Page Content */}
      <div className="p-4">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/inventory" element={<InventoryPage />} />
          <Route path="/forecast" element={<ForecastPage />} />
        </Routes>
      </div>

    </Router>
  );
}

export default App;