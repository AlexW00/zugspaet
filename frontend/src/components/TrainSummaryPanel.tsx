import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api } from '../api/client';
import type { DelayStatistics, TimeBasedDelay } from '../api/types';
import { Skeleton } from './Skeleton';

interface TrainSummaryPanelProps {
  station?: string;
  train_name?: string;
  isLoading?: boolean;
}

interface DelayCategory {
  name: string;
  value: number;
  color: string;
}

const getDelayColor = (delay: number) => {
  if (delay <= 5) return '#22c55e'; // green
  if (delay <= 15) return '#eab308'; // yellow
  return '#ef4444'; // red
};

export function TrainSummaryPanel({ station, train_name, isLoading = false }: TrainSummaryPanelProps) {
  const { t } = useTranslation();
  const [stats, setStats] = useState<DelayStatistics | null>(null);
  const [timeDelays, setTimeDelays] = useState<TimeBasedDelay[]>([]);
  const [isLoadingStats, setIsLoadingStats] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchStats() {
      if (!station && !train_name) return;
      
      setIsLoadingStats(true);
      setError(null);
      try {
        const [statsData, timeData] = await Promise.all([
          api.getDelayStatistics({ station, train_name }),
          api.getDelaysByTime({ 
            station, 
            train_name,
            group_by: 'day'
          })
        ]);
        setStats(statsData);
        setTimeDelays(timeData);
      } catch (error) {
        console.error('Failed to fetch statistics:', error);
        setError(t('errors.loadStatistics'));
      } finally {
        setIsLoadingStats(false);
      }
    }

    fetchStats();
  }, [station, train_name, t]);

  if (isLoading || isLoadingStats) {
    return (
      <div className="space-y-6">
        <Skeleton type="summary" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Skeleton type="chart" />
          <Skeleton type="chart" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md bg-red-50 p-4">
        <div className="flex">
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">
              {error}
            </h3>
          </div>
        </div>
      </div>
    );
  }

  if (!stats || stats.total_arrivals === 0) {
    return null;
  }

  // Prepare data for pie chart
  const delayCategories: DelayCategory[] = [
    {
      name: t('trainSummary.delayCategories.onTime'),
      value: stats.ontime_arrivals,
      color: '#22c55e' // green
    },
    {
      name: t('trainSummary.delayCategories.delayed'),
      value: stats.delayed_arrivals,
      color: '#ef4444' // red
    }
  ];

  // Transform time-based data for the line chart
  const timelineData = timeDelays.map(delay => ({
    time: `${delay.time_group}:00`,
    delay: delay.avg_delay,
    color: getDelayColor(delay.avg_delay),
    total: delay.total_arrivals,
    delayed: delay.delayed_arrivals
  }));

  return (
    <div className="mt-6 mb-8 bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">{t('trainSummary.title')}</h2>
      
      {/* Statistics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm text-gray-500">{t('trainSummary.totalArrivals')}</div>
          <div className="text-2xl font-semibold text-gray-900">{stats.total_arrivals}</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm text-gray-500">{t('trainSummary.averageDelay')}</div>
          <div className="text-2xl font-semibold" style={{ color: getDelayColor(stats.avg_delay) }}>
            {stats.avg_delay} {t('trainSummary.minutes')}
          </div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm text-gray-500">{t('trainSummary.medianDelay')}</div>
          <div className="text-2xl font-semibold" style={{ color: getDelayColor(stats.median_delay) }}>
            {stats.median_delay} {t('trainSummary.minutes')}
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pie Chart */}
        <div className="h-[400px] flex flex-col">
          <h3 className="text-sm font-medium text-gray-700 mb-2">{t('trainSummary.delayDistribution')}</h3>
          <div className="flex-grow">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={delayCategories}
                  cx="50%"
                  cy="45%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {delayCategories.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number) => [`${value} ${t('trainSummary.tooltips.trains')}`, '']}
                  contentStyle={{ backgroundColor: 'white', border: '1px solid #ccc' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap justify-center gap-4 mt-4 pb-2">
            {delayCategories.map((category, index) => (
              <div key={index} className="flex items-center">
                <div className="w-3 h-3 rounded-full mr-2" style={{ backgroundColor: category.color }} />
                <span className="text-sm text-gray-600">{category.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Line Chart */}
        <div className="h-[400px] flex flex-col">
          <h3 className="text-sm font-medium text-gray-700 mb-2">{t('trainSummary.delayTimeline')}</h3>
          <div className="flex-grow">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timelineData} margin={{ right: 30, bottom: 30 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 11 }}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  label={{ value: t('trainSummary.delayMinutes'), angle: -90, position: 'insideLeft', offset: -10 }}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: 'white', border: '1px solid #ccc', padding: '10px' }}
                  labelStyle={{ fontSize: 12, fontWeight: 'bold', marginBottom: '8px' }}
                  formatter={(value: any, name: string, props: any) => {
                    if (!props?.payload) return [value, name];
                    const { total, delayed } = props.payload;
                    
                    return [
                      <div key="tooltip-content">
                        <div style={{ marginBottom: '8px' }}>
                          {t('trainSummary.tooltips.averageDelay')}: {value} {t('trainSummary.tooltips.minutes')}
                        </div>
                        <div style={{ fontSize: '11px' }}>
                          <div>{t('trainSummary.tooltips.totalArrivals')}: {total}</div>
                          <div>{t('trainSummary.tooltips.delayedArrivals')}: {delayed}</div>
                        </div>
                      </div>,
                      ''
                    ];
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="delay"
                  stroke="#6b7280"
                  strokeWidth={2}
                  dot={(props: any) => {
                    const { cx, cy, payload } = props;
                    return (
                      <circle
                        cx={cx}
                        cy={cy}
                        r={4}
                        fill={payload.color}
                        stroke="none"
                      />
                    );
                  }}
                  activeDot={(props: any) => {
                    const { cx, cy, payload } = props;
                    return (
                      <circle
                        cx={cx}
                        cy={cy}
                        r={6}
                        fill={payload.color}
                        stroke="white"
                        strokeWidth={2}
                      />
                    );
                  }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
} 