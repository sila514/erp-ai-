import { BrowserRouter, Routes, Route } from "react-router-dom";
import DashboardLayout from "@/layouts/DashboardLayout";
import Dashboard from "@/modules/dashboard/Dashboard";
import InventoryPage from "@/modules/inventory/InventoryPage";
import SalesPage from "@/modules/sales/SalesPage";
import CustomersPage from "@/modules/customers/CustomersPage";
import FinancePage from "@/modules/finance/FinancePage";
import AnalyticsPage from "@/modules/analytics/AnalyticsPage";
import CopilotPage from "@/modules/copilot/CopilotPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<DashboardLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="inventory" element={<InventoryPage />} />
          <Route path="sales" element={<SalesPage />} />
          <Route path="customers" element={<CustomersPage />} />
          <Route path="finance" element={<FinancePage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="copilot" element={<CopilotPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
