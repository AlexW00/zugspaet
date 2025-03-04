import { ChevronDownIcon, ChevronUpIcon, InformationCircleIcon } from '@heroicons/react/20/solid';
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { TrainArrival } from '../api/types';
import { Skeleton } from './Skeleton';

interface TrainArrivalsTableProps {
  arrivals: TrainArrival[];
  isLoading?: boolean;
}

type SortField = 'time' | 'delay' | 'destination';
type SortDirection = 'asc' | 'desc';

interface SortConfig {
  field: SortField;
  direction: SortDirection;
}

const ITEMS_PER_PAGE = 50;

const getStatusStyle = (arrival: TrainArrival) => {
  if (arrival.is_canceled) {
    return 'bg-gray-100 text-gray-800'; // gray for canceled
  }
  if (arrival.delay_in_min <= 5) {
    return 'bg-green-100 text-green-800'; // green for on time
  }
  if (arrival.delay_in_min <= 15) {
    return 'bg-yellow-100 text-yellow-800'; // yellow for slight delay
  }
  return 'bg-red-100 text-red-800'; // red for major delay
};

const getStatusText = (arrival: TrainArrival, t: (key: string) => string) => {
  if (arrival.is_canceled) {
    return t('trainTable.status.canceled');
  }
  if (arrival.delay_in_min <= 5) {
    return t('trainTable.status.onTime');
  }
  if (arrival.delay_in_min <= 15) {
    return t('trainTable.status.slightDelay');
  }
  return t('trainTable.status.majorDelay');
};

export function TrainArrivalsTable({ arrivals, isLoading = false }: TrainArrivalsTableProps) {
  const { t } = useTranslation();
  const [sortConfig, setSortConfig] = useState<SortConfig>({ field: 'time', direction: 'desc' });
  const [displayCount, setDisplayCount] = useState(ITEMS_PER_PAGE);

  const handleSort = (field: SortField) => {
    setSortConfig(current => ({
      field,
      direction: current.field === field && current.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const sortedArrivals = useMemo(() => {
    const sorted = [...arrivals].sort((a, b) => {
      const direction = sortConfig.direction === 'asc' ? 1 : -1;
      
      switch (sortConfig.field) {
        case 'time':
          return direction * (new Date(a.time).getTime() - new Date(b.time).getTime());
        case 'delay':
          return direction * (a.delay_in_min - b.delay_in_min);
        case 'destination':
          return direction * a.final_destination_station.localeCompare(b.final_destination_station);
        default:
          return 0;
      }
    });
    return sorted;
  }, [arrivals, sortConfig]);

  const displayedArrivals = sortedArrivals.slice(0, displayCount);
  const hasMore = displayCount < sortedArrivals.length;

  const handleLoadMore = () => {
    setDisplayCount(current => Math.min(current + ITEMS_PER_PAGE, sortedArrivals.length));
  };

  if (isLoading) {
    return <Skeleton />;
  }

  if (arrivals.length === 0) {
    return (
      <div className="flex items-center justify-center text-gray-500 py-8">
        <InformationCircleIcon className="h-5 w-5 mr-2" />
        <span>{t('trainTable.noResults')}</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      <div className="-my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
        <div className="py-2 align-middle inline-block min-w-full sm:px-6 lg:px-8">
          <div className="shadow overflow-hidden border-b border-gray-200 sm:rounded-lg">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                    onClick={() => handleSort('time')}
                  >
                    <div className="flex items-center">
                      {t('trainTable.headers.time')}
                      {sortConfig.field === 'time' && (
                        sortConfig.direction === 'asc' ? <ChevronUpIcon className="w-4 h-4 ml-1" /> : <ChevronDownIcon className="w-4 h-4 ml-1" />
                      )}
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                    onClick={() => handleSort('delay')}
                  >
                    <div className="flex items-center">
                      {t('trainTable.headers.delay')}
                      {sortConfig.field === 'delay' && (
                        sortConfig.direction === 'asc' ? <ChevronUpIcon className="w-4 h-4 ml-1" /> : <ChevronDownIcon className="w-4 h-4 ml-1" />
                      )}
                    </div>
                  </th>
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                    onClick={() => handleSort('destination')}
                  >
                    <div className="flex items-center">
                      {t('trainTable.headers.destination')}
                      {sortConfig.field === 'destination' && (
                        sortConfig.direction === 'asc' ? <ChevronUpIcon className="w-4 h-4 ml-1" /> : <ChevronDownIcon className="w-4 h-4 ml-1" />
                      )}
                    </div>
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {t('trainTable.headers.status')}
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {displayedArrivals.map((arrival) => (
                  <tr key={`${arrival.time}-${arrival.final_destination_station}`}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(arrival.time).toLocaleString('de-DE', {
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`inline-flex rounded-full px-2 text-xs font-semibold leading-5 ${getStatusStyle(arrival)}`}>
                        {arrival.delay_in_min} min
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {arrival.final_destination_station}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`inline-flex rounded-full px-2 text-xs font-semibold leading-5 ${getStatusStyle(arrival)}`}>
                        {getStatusText(arrival, t)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {hasMore && (
              <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
                <button
                  onClick={handleLoadMore}
                  className="w-full flex justify-center items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-db-red-500"
                >
                  {t('trainTable.loadMore', 'Load More')}
                  <span className="ml-1 text-gray-500">
                    ({displayCount} / {sortedArrivals.length})
                  </span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 