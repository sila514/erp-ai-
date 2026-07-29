import { useEffect } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";

/** DashboardLayout'u sarar: token doğrulanana kadar bekletir, yoksa /login'e yönlendirir. */
export default function ProtectedRoute() {
  const { status, hydrate } = useAuthStore();
  const location = useLocation();

  useEffect(() => {
    if (status === "idle") hydrate();
  }, [status, hydrate]);

  if (status === "idle" || status === "loading") {
    return (
      <div className="flex h-screen items-center justify-center bg-navy-950 text-[13px] text-slate-400">
        Yükleniyor...
      </div>
    );
  }

  if (status === "unauthenticated") {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}
