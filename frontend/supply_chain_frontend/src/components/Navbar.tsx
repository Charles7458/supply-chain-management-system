import { Link, useLocation } from "react-router-dom";

const Navbar = () => {
  const location = useLocation();

  const navItems = [
    { name: "Dashboard", path: "/" },
    { name: "Inventory", path: "/inventory" },
    { name: "Forecast", path: "/forecast" }
  ];

  return (
    <nav className="bg-white shadow-md px-6 py-3 flex justify-between items-center">

      {/* 🔹 Logo / Title */}
      <h1 className="text-xl font-bold text-blue-600">
        SupplyChain AI
      </h1>

      {/* 🔹 Navigation Links */}
      <div className="flex space-x-6">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;

          return (
            <Link
              key={item.name}
              to={item.path}
              className={`text-sm font-medium transition ${
                isActive
                  ? "text-blue-600 border-b-2 border-blue-600 pb-1"
                  : "text-gray-600 hover:text-blue-500"
              }`}
            >
              {item.name}
            </Link>
          );
        })}
      </div>
    </nav>
  );
};

export default Navbar;