import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from './api/client';
import type { TrainArrival } from './api/types';
import { Footer } from './components/Footer';
import { LanguageToggle } from './components/LanguageToggle';
import { SearchableSelect } from './components/SearchableSelect';
import { TrainArrivalsTable } from './components/TrainArrivalsTable';
import { TrainSummaryPanel } from './components/TrainSummaryPanel';

function useUrlParams() {
  // Get initial values from URL
  const params = new URLSearchParams(window.location.search);
  const [selectedStation, setSelectedStation] = useState(params.get('station') || '');
  const [selectedTrain, setSelectedTrain] = useState(params.get('train') || '');

  // Update URL when values change
  const updateStation = (station: string) => {
    const params = new URLSearchParams(window.location.search);
    if (station) {
      params.set('station', station);
    } else {
      params.delete('station');
    }
    params.delete('train'); // Reset train when station changes
    window.history.replaceState({}, '', `${window.location.pathname}?${params}`);
    setSelectedStation(station);
  };

  const updateTrain = (train: string) => {
    const params = new URLSearchParams(window.location.search);
    if (train) {
      params.set('train', train);
    } else {
      params.delete('train');
    }
    window.history.replaceState({}, '', `${window.location.pathname}?${params}`);
    setSelectedTrain(train);
  };

  return {
    selectedStation,
    selectedTrain,
    updateStation,
    updateTrain
  };
}

function App() {
  const { t } = useTranslation();
  const [stations, setStations] = useState<string[]>([]);
  const [trains, setTrains] = useState<string[]>([]);
  const [arrivals, setArrivals] = useState<TrainArrival[]>([]);
  
  const { selectedStation, selectedTrain, updateStation, updateTrain } = useUrlParams();
  
  const [isLoadingStations, setIsLoadingStations] = useState(true);
  const [isLoadingTrains, setIsLoadingTrains] = useState(false);
  const [isLoadingArrivals, setIsLoadingArrivals] = useState(false);
  const [error, setError] = useState('');

  // Load stations on mount
  useEffect(() => {
    const loadStations = async () => {
      try {
        const data = await api.getTrainStations();
        setStations(data);
        
        // If we have a station in URL but it's not valid, clear it
        if (selectedStation && !data.includes(selectedStation)) {
          updateStation('');
        }
      } catch {
        setError(t('errors.loadStations'));
      } finally {
        setIsLoadingStations(false);
      }
    };
    loadStations();
  }, [t]);

  // Load trains when station changes
  useEffect(() => {
    if (!selectedStation) {
      setTrains([]);
      return;
    }

    const loadTrains = async () => {
      setIsLoadingTrains(true);
      try {
        const data = await api.getTrains(selectedStation);
        setTrains(data);
        
        // If we have a train in URL but it's not valid for this station, clear it
        if (selectedTrain && !data.includes(selectedTrain)) {
          updateTrain('');
        }
      } catch {
        setError(t('errors.loadTrains'));
      } finally {
        setIsLoadingTrains(false);
      }
    };
    loadTrains();
  }, [selectedStation, t]);

  // Load arrivals when either station or train changes
  useEffect(() => {
    if (!selectedStation || !selectedTrain) {
      setArrivals([]);
      return;
    }

    const loadArrivals = async () => {
      setIsLoadingArrivals(true);
      setError('');
      try {
        const data = await api.getTrainArrivals(selectedStation, selectedTrain);
        setArrivals(data);
      } catch {
        setError(t('errors.loadArrivals'));
      } finally {
        setIsLoadingArrivals(false);
      }
    };
    loadArrivals();
  }, [selectedStation, selectedTrain, t]);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-db-red-600 shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-white">
              <a href="/" className="hover:text-gray-100 transition-colors">
                {t('app.title', 'Will I be late?')}
              </a>
            </h1>
            <div className="flex items-center space-x-4">
              <a
                href="https://github.com/AlexW00/zugspaet"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center rounded-md bg-white/10 px-3 py-2 text-sm font-semibold text-white shadow-sm ring-1 ring-inset ring-white/10 hover:bg-white/20"
              >
                <svg className="h-5 w-5 mr-1" aria-hidden="true" fill="currentColor" viewBox="0 0 24 24">
                  <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                </svg>
                GitHub
              </a>
              <LanguageToggle />
            </div>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="space-y-4">
              <div>
                <label htmlFor="station" className="block text-sm font-medium text-gray-700">
                  {t('form.station.label')}
                </label>
                <div className="mt-1">
                  <SearchableSelect
                    options={stations}
                    value={selectedStation}
                    onChange={updateStation}
                    placeholder={t('form.station.placeholder')}
                    isLoading={isLoadingStations}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="train" className="block text-sm font-medium text-gray-700">
                  {t('form.train.label')}
                </label>
                <div className="mt-1">
                  <SearchableSelect
                    options={trains}
                    value={selectedTrain}
                    onChange={updateTrain}
                    placeholder={t('form.train.placeholder')}
                    isLoading={isLoadingTrains}
                    disabled={!selectedStation}
                  />
                </div>
              </div>

              {error && (
                <div className="rounded-md bg-red-50 p-4">
                  <div className="flex">
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-red-800">
                        {error}
                      </h3>
                    </div>
                  </div>
                </div>
              )}

              <TrainSummaryPanel arrivals={arrivals} />

              <TrainArrivalsTable
                arrivals={arrivals}
                isLoading={isLoadingArrivals}
              />
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}

export default App;
