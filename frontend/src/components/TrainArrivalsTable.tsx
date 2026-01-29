import { ChevronDownIcon, ChevronUpIcon, InformationCircleIcon } from '@heroicons/react/20/solid';
import { useState } from 'react';
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

interface HeaderCellProps {
  field: SortField;
  label: string;
  currentSort: SortConfig;
  onSort: (field: SortField) => void;
}

function HeaderCell({ field, label, currentSort, onSort }: HeaderCellProps) {
  const isActive = currentSort.field === field;

  return (
    <th
      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
      onClick={() => onSort(field)}
    >
      <div className="flex items-center gap-1">
        <span>{label}</span>
        <span className="inline-flex flex-none items-center">
          {isActive && currentSort.direction === 'asc' && (
            <ChevronUpIcon className="h-4 w-4" />
          )}
          {isActive && currentSort.direction === 'desc' && (
            <ChevronDownIcon className="h-4 w-4" />
          )}
          {!isActive && (
            <ChevronUpIcon className="h-4 w-4 text-gray-300" />
          )}
        </span>
      </div>
    </th>
  );
}

const getStatusStyle = (arrival: TrainArrival) => {
  if (arrival.isCanceled) {
    return 'bg-gray-100 text-gray-800'; // gray for canceled
  }
  if (arrival.delayInMin <= 5) {
    return 'bg-green-100 text-green-800'; // green for on time
  }
  if (arrival.delayInMin <= 20) {
    return 'bg-yellow-100 text-yellow-800'; // yellow for slight delay
  }
  return 'bg-red-100 text-red-800'; // red for major delay
};

const getStatusText = (arrival: TrainArrival, t: (key: string) => string) => {
  if (arrival.isCanceled) {
    return t('trainTable.status.canceled');
  }
  if (arrival.delayInMin <= 5) {
    return t('trainTable.status.onTime');
  }
  if (arrival.delayInMin <= 20) {
    return t('trainTable.status.slightDelay');
  }
  return t('trainTable.status.majorDelay');
};

export function TrainArrivalsTable({ arrivals, isLoading = false }: TrainArrivalsTableProps) {
  const { t } = useTranslation();
  const [sortConfig, setSortConfig] = useState<SortConfig>({ field: 'time', direction: 'desc' });

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

  const handleSort = (field: SortField) => {
    setSortConfig(current => ({
      field,
      direction: current.field === field && current.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const sortedArrivals = [...arrivals].sort((a, b) => {
    const direction = sortConfig.direction === 'asc' ? 1 : -1;

    switch (sortConfig.field) {
      case 'time':
        return direction * (new Date(a.time).getTime() - new Date(b.time).getTime());
      case 'delay':
        return direction * (a.delayInMin - b.delayInMin);
      case 'destination':
        return direction * a.finalDestinationStation.localeCompare(b.finalDestinationStation);
      default:
        return 0;
    }
  });

  return (
    <div className={`${arrivals.length > 15 ? 'h-[600px]' : ''} overflow-x-auto relative`}>
      <table className="min-w-full divide-y divide-gray-300">
        <thead className={`bg-white ${arrivals.length > 15 ? 'sticky top-0 z-10' : ''}`}>
          <tr>
            <HeaderCell
              field="time"
              currentSort={sortConfig}
              onSort={handleSort}
              label={t('trainTable.columns.time')}
            />
            <HeaderCell
              field="delay"
              currentSort={sortConfig}
              onSort={handleSort}
              label={t('trainTable.columns.delay')}
            />
            <HeaderCell
              field="destination"
              currentSort={sortConfig}
              onSort={handleSort}
              label={t('trainTable.columns.destination')}
            />
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              {t('trainTable.columns.status')}
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {sortedArrivals.map((arrival) => (
            <tr key={`${arrival.time}-${arrival.finalDestinationStation}`}>
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
                <span
                  className={`inline-flex rounded-full px-2 text-xs font-semibold leading-5 ${arrival.delayInMin <= 5
                      ? 'bg-green-100 text-green-800'
                      : arrival.delayInMin <= 20
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                >
                  {arrival.delayInMin} min
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                {arrival.finalDestinationStation}
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
    </div>
  );
} 