import { useTranslation } from 'react-i18next';
import { CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { TrainArrival } from '../api/types';
import { Skeleton } from './Skeleton';

interface TrainSummaryPanelProps {
  arrivals: TrainArrival[];
  isLoading?: boolean;
}

interface DelayCategory {
  name: string;
  value: number;
  color: string;
}

interface TimelineDataPoint {
  time: string;
  delay: number;
  color: string;
  rides: {
    delay: number;
    color: string;
    time: string;
  }[];
}

const getDelayColor = (delay: number) => {
  if (delay <= 5) return '#22c55e'; // green
  if (delay <= 15) return '#eab308'; // yellow
  return '#ef4444'; // red
};

export function TrainSummaryPanel({ arrivals, isLoading = false }: TrainSummaryPanelProps) {
  const { t } = useTranslation();

  if (isLoading) {
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

  if (arrivals.length === 0) {
    return null;
  }

  // Calculate statistics
  const canceledCount = arrivals.filter(a => a.is_canceled).length;
  const activeArrivals = arrivals.filter(a => !a.is_canceled);
  const totalArrivals = activeArrivals.length;
  const avgDelay = Math.round(activeArrivals.reduce((acc, curr) => acc + curr.delay_in_min, 0) / totalArrivals);

  // Prepare data for pie chart
  const delayCategories: DelayCategory[] = [
    {
      name: t('trainSummary.delayCategories.onTime'),
      value: arrivals.filter(a => !a.is_canceled && a.delay_in_min <= 5).length,
      color: '#22c55e' // green
    },
    {
      name: t('trainSummary.delayCategories.slightDelay'),
      value: arrivals.filter(a => !a.is_canceled && a.delay_in_min > 5 && a.delay_in_min <= 15).length,
      color: '#eab308' // yellow
    },
    {
      name: t('trainSummary.delayCategories.majorDelay'),
      value: arrivals.filter(a => !a.is_canceled && a.delay_in_min > 15).length,
      color: '#ef4444' // red
    },
    {
      name: t('trainSummary.delayCategories.canceled'),
      color: '#6b7280', // gray-500
      value: canceledCount
    }
  ];

  // Prepare data for line chart
  const timelineData = arrivals
    .filter(a => !a.is_canceled)
    .reduce((acc: { [key: string]: TimelineDataPoint }, arrival) => {
      const dayKey = new Date(arrival.time).toLocaleDateString('de-DE', {
        month: 'numeric',
        day: 'numeric'
      }).replace(/\.$/, ''); // Remove trailing dot
      
      const rideInfo = {
        delay: arrival.delay_in_min,
        color: getDelayColor(arrival.delay_in_min),
        time: new Date(arrival.time).toLocaleTimeString('de-DE', {
          hour: '2-digit',
          minute: '2-digit'
        })
      };

      if (!acc[dayKey]) {
        acc[dayKey] = {
          time: dayKey,
          delay: arrival.delay_in_min,
          color: getDelayColor(arrival.delay_in_min),
          rides: [rideInfo]
        };
      } else {
        acc[dayKey].rides.push(rideInfo);
        // Update average delay
        const totalDelay = acc[dayKey].rides.reduce((sum, ride) => sum + ride.delay, 0);
        acc[dayKey].delay = Math.round(totalDelay / acc[dayKey].rides.length);
        acc[dayKey].color = getDelayColor(acc[dayKey].delay);
      }
      
      return acc;
    }, {});

  const groupedTimelineData = Object.values(timelineData)
    .sort((a, b) => {
      const dateA = a.time.split('.').reverse().join('');
      const dateB = b.time.split('.').reverse().join('');
      return dateA.localeCompare(dateB);
    });

  return (
    <div className="mt-6 mb-8 bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">{t('trainSummary.title')}</h2>
      
      {/* Statistics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm text-gray-500">{t('trainSummary.totalArrivals')}</div>
          <div className="text-2xl font-semibold text-gray-900">{totalArrivals}</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm text-gray-500">{t('trainSummary.averageDelay')}</div>
          <div className="text-2xl font-semibold" style={{ color: getDelayColor(avgDelay) }}>
            {avgDelay} {t('trainSummary.minutes')}
          </div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm text-gray-500">{t('trainSummary.canceledTrains')}</div>
          <div className="text-2xl font-semibold" style={{ color: canceledCount > 0 ? '#ef4444' : '#22c55e' }}>
            {canceledCount}
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
              <LineChart data={groupedTimelineData} margin={{ right: 30, bottom: 30 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 11 }}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                  interval={Math.ceil(groupedTimelineData.length / 8)}
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
                    const rides = props.payload.rides;
                    if (!rides) return [`${value} ${t('trainSummary.tooltips.minutes')}`, t('trainSummary.tooltips.delay')];
                    
                    return [
                      <div key="tooltip-content">
                        <div style={{ marginBottom: '8px' }}>
                          {t('trainSummary.tooltips.averageDelay')}: {value} {t('trainSummary.tooltips.minutes')}
                        </div>
                        <div style={{ fontSize: '11px' }}>
                          {rides.slice(0, 5).map((ride: { time: string; delay: number; color: string }, idx: number) => (
                            <div key={idx} style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
                              <div
                                style={{
                                  width: '8px',
                                  height: '8px',
                                  borderRadius: '50%',
                                  backgroundColor: ride.color,
                                  marginRight: '6px'
                                }}
                              />
                              <span>{ride.time}: {ride.delay} {t('trainSummary.tooltips.minutes')}</span>
                            </div>
                          ))}
                          {rides.length > 5 && (
                            <div style={{ 
                              color: '#6b7280',
                              fontSize: '10px',
                              fontStyle: 'italic',
                              marginTop: '2px',
                              textAlign: 'center'
                            }}>
                              +{rides.length - 5} {t('trainSummary.tooltips.more')}
                            </div>
                          )}
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
                  dot={({ cx, cy, payload }: { cx?: number; cy?: number; payload?: TimelineDataPoint }) => (
                    <circle
                      cx={cx ?? 0}
                      cy={cy ?? 0}
                      r={4}
                      fill={payload?.color ?? '#6b7280'}
                      stroke="none"
                    />
                  )}
                  activeDot={({ cx, cy, payload }: { cx?: number; cy?: number; payload?: TimelineDataPoint }) => (
                    <circle
                      cx={cx ?? 0}
                      cy={cy ?? 0}
                      r={6}
                      fill={payload?.color ?? '#6b7280'}
                      stroke="white"
                      strokeWidth={2}
                    />
                  )}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
} 