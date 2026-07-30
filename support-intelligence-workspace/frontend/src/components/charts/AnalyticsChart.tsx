import type { ReactNode } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { titleCase } from "@/lib/utils";

/** Muted enterprise palette — no purple */
const COLORS = [
  "hsl(var(--foreground))",
  "hsl(240 4% 34%)",
  "hsl(240 4% 46%)",
  "hsl(152 60% 32%)",
  "hsl(32 90% 40%)",
  "hsl(0 72% 46%)",
];
const CHART_STROKE = "hsl(var(--foreground))";
const CHART_FILL = "hsl(var(--foreground))";

const tooltipStyle = {
  background: "hsl(var(--card))",
  border: "1px solid hsl(var(--border))",
  borderRadius: 6,
  fontSize: 12,
  boxShadow: "var(--shadow-sm)",
  padding: "8px 10px",
};

const axisTick = { fontSize: 11, fill: "hsl(var(--muted-foreground))" };

export function TrendLineChart({
  title,
  data,
  dataKey = "value",
  nameKey = "name",
}: {
  title: string;
  data: { name: string; value: number }[];
  dataKey?: string;
  nameKey?: string;
}) {
  return (
    <ChartPanel title={title} empty={!data.length}>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={CHART_FILL} stopOpacity={0.12} />
              <stop offset="100%" stopColor={CHART_FILL} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid
            strokeDasharray="3 3"
            vertical={false}
            stroke="hsl(var(--border))"
          />
          <XAxis
            dataKey={nameKey}
            tick={axisTick}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            allowDecimals={false}
            tick={axisTick}
            width={32}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip contentStyle={tooltipStyle} />
          <Area
            type="monotone"
            dataKey={dataKey}
            stroke={CHART_STROKE}
            fill="url(#trendFill)"
            strokeWidth={1.75}
          />
        </AreaChart>
      </ResponsiveContainer>
    </ChartPanel>
  );
}

export function DistributionBarChart({
  title,
  data,
}: {
  title: string;
  data: Record<string, number>;
}) {
  const rows = Object.entries(data).map(([key, count]) => ({
    name: titleCase(key),
    count,
  }));

  return (
    <ChartPanel title={title} empty={!rows.length}>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={rows} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid
            strokeDasharray="3 3"
            vertical={false}
            stroke="hsl(var(--border))"
          />
          <XAxis
            dataKey="name"
            tick={axisTick}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            allowDecimals={false}
            tick={axisTick}
            width={32}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip contentStyle={tooltipStyle} />
          <Bar dataKey="count" fill={CHART_FILL} radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartPanel>
  );
}

export function NamedCountBarChart({
  title,
  items,
}: {
  title: string;
  items: { key: string; count: number; label?: string | null }[];
}) {
  const rows = items.slice(0, 8).map((i) => ({
    name: i.label || i.key,
    count: i.count,
  }));

  return (
    <ChartPanel title={title} empty={!rows.length}>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart
          data={rows}
          layout="vertical"
          margin={{ top: 8, right: 8, left: 8, bottom: 0 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            horizontal={false}
            stroke="hsl(var(--border))"
          />
          <XAxis
            type="number"
            allowDecimals={false}
            tick={axisTick}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={110}
            tick={axisTick}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip contentStyle={tooltipStyle} />
          <Bar dataKey="count" fill={CHART_FILL} radius={[0, 2, 2, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartPanel>
  );
}

export function DistributionPieChart({
  title,
  data,
}: {
  title: string;
  data: Record<string, number>;
}) {
  const rows = Object.entries(data).map(([key, value]) => ({
    name: titleCase(key),
    value,
  }));

  return (
    <ChartPanel title={title} empty={!rows.length}>
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie
            data={rows}
            dataKey="value"
            nameKey="name"
            innerRadius={48}
            outerRadius={74}
            paddingAngle={2}
            stroke="hsl(var(--card))"
            strokeWidth={2}
          >
            {rows.map((_, i) => (
              <Cell key={rows[i]?.name} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip contentStyle={tooltipStyle} />
        </PieChart>
      </ResponsiveContainer>
      {rows.length ? (
        <ul className="mt-2 flex flex-wrap gap-x-3 gap-y-1">
          {rows.map((r, i) => (
            <li
              key={r.name}
              className="flex items-center gap-1.5 text-[11px] text-muted-foreground"
            >
              <span
                className="h-2 w-2 rounded-[2px]"
                style={{ background: COLORS[i % COLORS.length] }}
                aria-hidden
              />
              {r.name}
              <span className="tabular text-foreground">{r.value}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </ChartPanel>
  );
}

function ChartPanel({
  title,
  empty,
  children,
}: {
  title: string;
  empty?: boolean;
  children: ReactNode;
}) {
  return (
    <div className="panel p-4">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h3 className="text-[13px] font-semibold tracking-tight text-foreground">
          {title}
        </h3>
      </div>
      {empty ? (
        <p className="py-12 text-center text-[13px] text-muted-foreground">
          No data yet
        </p>
      ) : (
        children
      )}
    </div>
  );
}
