import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Suspense, lazy } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Toaster } from "sonner";
import { AppShell } from "@/components/layout/AppShell";
import { Skeleton } from "@/components/ui/states";
import { ThemeProvider } from "@/context/theme";

const DashboardPage = lazy(() =>
  import("@/features/dashboard/DashboardPage").then((m) => ({
    default: m.DashboardPage,
  })),
);
const AskPage = lazy(() =>
  import("@/features/ask/AskPage").then((m) => ({ default: m.AskPage })),
);
const GapsPage = lazy(() =>
  import("@/features/gaps/GapsPage").then((m) => ({ default: m.GapsPage })),
);
const DocumentsPage = lazy(() =>
  import("@/features/documents/DocumentsPage").then((m) => ({
    default: m.DocumentsPage,
  })),
);
const AnalyticsPage = lazy(() =>
  import("@/features/analytics/AnalyticsPage").then((m) => ({
    default: m.AnalyticsPage,
  })),
);
const SettingsPage = lazy(() =>
  import("@/features/settings/SettingsPage").then((m) => ({
    default: m.SettingsPage,
  })),
);

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function PageFallback() {
  return (
    <div className="mx-auto max-w-[1280px] space-y-5">
      <div className="space-y-2 border-b border-border pb-4">
        <Skeleton className="h-7 w-40" />
        <Skeleton className="h-4 w-80 max-w-full" />
      </div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Skeleton className="h-[88px]" />
        <Skeleton className="h-[88px]" />
        <Skeleton className="h-[88px]" />
        <Skeleton className="h-[88px]" />
      </div>
      <Skeleton className="h-64 w-full" />
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <Suspense fallback={<PageFallback />}>
          <Routes>
            <Route element={<AppShell />}>
              <Route index element={<DashboardPage />} />
              <Route path="ask" element={<AskPage />} />
              <Route path="gaps" element={<GapsPage />} />
              <Route path="documents" element={<DocumentsPage />} />
              <Route path="analytics" element={<AnalyticsPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
        <Toaster
          position="top-right"
          closeButton
          toastOptions={{
            className: "text-[13px]",
            style: {
              borderRadius: 6,
              border: "1px solid hsl(var(--border))",
              fontFamily: "Plus Jakarta Sans, ui-sans-serif, system-ui",
            },
          }}
        />
      </ThemeProvider>
    </QueryClientProvider>
  );
}
