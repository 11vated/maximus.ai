import React from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { type ThemeConfig } from '../types/theme';

interface ChartDataPoint {
  [key: string]: string | number;
}

interface ChartRendererProps {
  data: ChartDataPoint[];
  type?: 'line' | 'bar';
  xKey?: string;
  dataKeys?: string[];
  theme: ThemeConfig;
  title?: string;
  height?: number;
}

const ChartRenderer: React.FC<ChartRendererProps> = ({
  data,
  type = 'line',
  xKey = 'name',
  dataKeys,
  theme,
  title,
  height = 300,
}) => {
  const keys = dataKeys || (data.length > 0 ? Object.keys(data[0]).filter(k => k !== xKey) : []);

  return (
    <div className="my-4 p-4 rounded-lg" style={{ background: theme.background + '80' }}>
      {title && (
        <h3 className="text-sm font-bold mb-3" style={{ color: theme.primary }}>
          {title}
        </h3>
      )}
      <ResponsiveContainer width="100%" height={height}>
        {type === 'line' ? (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke={theme.secondary + '20'} />
            <XAxis dataKey={xKey} tick={{ fill: theme.foreground, fontSize: 12 }} />
            <YAxis tick={{ fill: theme.foreground, fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                background: theme.background,
                border: `1px solid ${theme.primary}40`,
                color: theme.foreground,
              }}
            />
            <Legend wrapperStyle={{ color: theme.foreground }} />
            {keys.map((key, idx) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={idx === 0 ? theme.primary : idx === 1 ? theme.secondary : theme.accent}
                strokeWidth={2}
                dot={false}
              />
            ))}
          </LineChart>
        ) : (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke={theme.secondary + '20'} />
            <XAxis dataKey={xKey} tick={{ fill: theme.foreground, fontSize: 12 }} />
            <YAxis tick={{ fill: theme.foreground, fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                background: theme.background,
                border: `1px solid ${theme.primary}40`,
                color: theme.foreground,
              }}
            />
            <Legend wrapperStyle={{ color: theme.foreground }} />
            {keys.map((key, idx) => (
              <Bar
                key={key}
                dataKey={key}
                fill={idx === 0 ? theme.primary : idx === 1 ? theme.secondary : theme.accent}
              />
            ))}
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
};

export default ChartRenderer;
