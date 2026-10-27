import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { useState, useEffect } from "react";
import Home      from "./pages/Home";
import Input     from "./pages/Input";
import Dashboard from "./pages/Dashboard";

export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem("theme") || "dark");

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem("theme", theme);
  }, [theme]);

  const props = { theme, setTheme };
  return (
    <Router>
      <Routes>
        <Route path="/"          element={<Home      {...props} />} />
        <Route path="/input"     element={<Input     {...props} />} />
        <Route path="/dashboard" element={<Dashboard {...props} />} />
      </Routes>
    </Router>
  );
}
