import { apiClient } from "./client";

export interface DashboardOverview {
  total_products: number;
  low_stock_products: number;
  total_customers: number;
  flagged_anomalous_sales: number;
}

export async function fetchDashboardOverview(): Promise<DashboardOverview> {
  const { data } = await apiClient.get<DashboardOverview>("/api/dashboard/overview");
  return data;
}

export interface Product {
  id: string;
  sku: string;
  name: string;
  category: string | null;
  unit_price: number;
  unit_cost: number;
  stock_quantity: number;
  reorder_level: number;
  lead_time_days: number;
}

export async function fetchProducts(): Promise<Product[]> {
  const { data } = await apiClient.get<Product[]>("/api/inventory/products");
  return data;
}

export interface StockRisk {
  product_id: string;
  current_stock: number;
  predicted_daily_demand: number;
  days_until_stockout: number | null;
  risk_level: "low" | "medium" | "high";
  recommended_reorder_quantity: number;
}

export async function fetchStockRisk(productId: string): Promise<StockRisk> {
  const { data } = await apiClient.get<StockRisk>(`/api/inventory/products/${productId}/stock-risk`);
  return data;
}

export async function askCopilot(question: string): Promise<string> {
  const { data } = await apiClient.post<{ answer: string }>("/api/copilot/ask", { question });
  return data.answer;
}
