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

export interface SaleItem {
  product_id: string;
  quantity: number;
  unit_price: number;
}

export interface Sale {
  id: string;
  customer_id: string;
  status: "pending" | "completed" | "cancelled";
  total_amount: number;
  is_flagged_anomaly: boolean;
  anomaly_score: number | null;
  created_at: string;
  items: SaleItem[];
}

export async function fetchSales(): Promise<Sale[]> {
  const { data } = await apiClient.get<Sale[]>("/api/sales");
  return data;
}

export interface Customer {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  segment: string | null;
  churn_risk_score: number | null;
  lifetime_value: number | null;
}

export async function fetchCustomers(): Promise<Customer[]> {
  const { data } = await apiClient.get<Customer[]>("/api/customers");
  return data;
}

export interface ChurnRisk {
  customer_id: string;
  churn_probability: number;
  risk_level: string;
  top_factors: string[];
}

export async function fetchChurnRisk(customerId: string): Promise<ChurnRisk> {
  const { data } = await apiClient.get<ChurnRisk>(`/api/customers/${customerId}/churn-risk`);
  return data;
}

export interface CustomerSegmentAssignment {
  customer_id: string;
  segment: string;
  recency: number;
  frequency: number;
  monetary: number;
}

/** ml_service her müşteri için ayrı bir segment ataması döndürür (önceden toplanmış sayım değil). */
export async function fetchCustomerSegments(): Promise<{ customers: CustomerSegmentAssignment[] }> {
  const { data } = await apiClient.get<{ customers: CustomerSegmentAssignment[] }>(
    "/api/customers/segments/overview"
  );
  return data;
}

export interface FinanceTransaction {
  id: string;
  type: "income" | "expense";
  category: string | null;
  amount: number;
  description: string | null;
  created_at: string;
}

export async function fetchFinanceTransactions(): Promise<FinanceTransaction[]> {
  const { data } = await apiClient.get<FinanceTransaction[]>("/api/finance/transactions");
  return data;
}

export interface FinanceSummary {
  total_income: number;
  total_expense: number;
  net_profit: number;
}

export async function fetchFinanceSummary(): Promise<FinanceSummary> {
  const { data } = await apiClient.get<FinanceSummary>("/api/finance/summary");
  return data;
}

export async function askCopilot(question: string): Promise<string> {
  const { data } = await apiClient.post<{ answer: string }>("/api/copilot/ask", { question });
  return data.answer;
}
