import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from './api/client';
import type { TrainArrival } from './api/types';
import { Footer } from './components/Footer';
import { LanguageToggle } from './components/LanguageToggle';
import { MobileMenu } from './components/MobileMenu';
import { SearchableSelect } from './components/SearchableSelect';
import { TrainArrivalsTable } from './components/TrainArrivalsTable';
import { TrainSummaryPanel } from './components/TrainSummaryPanel';

// Separate the search form into its own component to prevent unnecessary re-renders
const SearchForm = ({
  stations,
  trains,
  selectedStation,
  selectedTrain,
  updateStation,
  updateTrain,
  isLoadingStations,
  isLoadingTrains,
}: {
  stations: string[];
  trains: string[];
  selectedStation: string;
  selectedTrain: string;
  updateStation: (station: string) => void;
  updateTrain: (train: string) => void;
  isLoadingStations: boolean;
  isLoadingTrains: boolean;
}) => {
  const { t } = useTranslation();

  return (
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
          />
        </div>
      </div>
    </div>
  );
};

function useUrlParams() {
  const params = new URLSearchParams(window.location.search);
  const [selectedStation, setSelectedStation] = useState(params.get('station') || '');
  const [selectedTrain, setSelectedTrain] = useState(params.get('train') || '');

  const updateStation = useCallback((station: string) => {
    const params = new URLSearchParams(window.location.search);
    if (station) {
      params.set('station', station);
    } else {
      params.delete('station');
    }
    params.delete('train'); // Reset train when station changes
    window.history.replaceState({}, '', `${window.location.pathname}?${params}`);
    setSelectedStation(station);
  }, []);

  const updateTrain = useCallback((train: string) => {
    const params = new URLSearchParams(window.location.search);
    if (train) {
      params.set('train', train);
    } else {
      params.delete('train');
    }
    window.history.replaceState({}, '', `${window.location.pathname}?${params}`);
    setSelectedTrain(train);
  }, []);

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
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  
  const { selectedStation, selectedTrain, updateStation, updateTrain } = useUrlParams();
  
  const [isLoadingStations, setIsLoadingStations] = useState(true);
  const [isLoadingTrains, setIsLoadingTrains] = useState(true);
  const [isLoadingArrivals, setIsLoadingArrivals] = useState(false);
  const [error, setError] = useState('');

  // Store initial suggestions
  const [initialStations, setInitialStations] = useState<string[]>([]);
  const [initialTrains, setInitialTrains] = useState<string[]>([]);

  // Load initial suggestions on mount
  useEffect(() => {
    const loadInitialSuggestions = async () => {
      try {
        const [stationsData, trainsData] = await Promise.all([
          api.getStations(),
          api.getTrains()
        ]);
        setInitialStations(stationsData);
        setInitialTrains(trainsData);
        setStations(stationsData);
        setTrains(trainsData);
      } catch {
        setError(t('errors.loadSuggestions'));
      } finally {
        setIsLoadingStations(false);
        setIsLoadingTrains(false);
      }
    };
    loadInitialSuggestions();
  }, []);

  // Update station suggestions only when train selection changes
  useEffect(() => {
    const loadStationSuggestions = async () => {
      if (!selectedTrain) {
        setStations(initialStations);
        return;
      }
      
      setIsLoadingStations(true);
      try {
        const data = await api.getStations(selectedTrain);
        setStations(data);
        
        // If current station is not in new suggestions, clear it
        if (selectedStation && !data.includes(selectedStation)) {
          updateStation('');
        }
      } catch {
        setError(t('errors.loadStations'));
      } finally {
        setIsLoadingStations(false);
      }
    };
    loadStationSuggestions();
  }, [selectedTrain, initialStations]);

  // Update train suggestions only when station selection changes
  useEffect(() => {
    const loadTrainSuggestions = async () => {
      if (!selectedStation) {
        setTrains(initialTrains);
        return;
      }
      
      setIsLoadingTrains(true);
      try {
        const data = await api.getTrains(selectedStation);
        setTrains(data);
        
        // If current train is not in new suggestions, clear it
        if (selectedTrain && !data.includes(selectedTrain)) {
          updateTrain('');
        }
      } catch {
        setError(t('errors.loadTrains'));
      } finally {
        setIsLoadingTrains(false);
      }
    };
    loadTrainSuggestions();
  }, [selectedStation, initialTrains]);

  // Memoize the arrivals loading callback
  const loadArrivals = useCallback(async () => {
    setIsLoadingArrivals(true);
    setError('');
    try {
      const data = await api.getArrivals({
        station: selectedStation,
        train_name: selectedTrain
      });
      setArrivals(data);
    } catch {
      setError(t('errors.loadArrivals'));
    } finally {
      setIsLoadingArrivals(false);
    }
  }, [selectedStation, selectedTrain, t]);

  // Load arrivals when either station or train changes
  useEffect(() => {
    if (selectedStation || selectedTrain) {
      loadArrivals();
    } else {
      setArrivals([]);
    }
  }, [loadArrivals, selectedStation, selectedTrain]);

  // Memoize the search form props
  const searchFormProps = useMemo(() => ({
    stations,
    trains,
    selectedStation,
    selectedTrain,
    updateStation,
    updateTrain,
    isLoadingStations,
    isLoadingTrains,
  }), [
    stations,
    trains,
    selectedStation,
    selectedTrain,
    updateStation,
    updateTrain,
    isLoadingStations,
    isLoadingTrains,
  ]);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-db-red-600 shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-white truncate flex-shrink">
              <a href="/" className="hover:text-gray-100 transition-colors inline-flex items-center">
                <img src="/train-front-white.svg" alt="Train icon" className="w-8 h-8 mr-2" />
                <span className="truncate">{t('app.title', 'Zugspaet.de')}</span>
              </a>
            </h1>
            {/* Desktop navigation */}
            <div className="hidden md:flex items-center space-x-4">
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
            {/* Mobile menu */}
            <div className="relative md:hidden">
              <MobileMenu isOpen={isMobileMenuOpen} setIsOpen={setIsMobileMenuOpen} />
            </div>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="space-y-4">
              <SearchForm {...searchFormProps} />

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

              {(selectedStation || selectedTrain) && (
                <>
                  <TrainSummaryPanel 
                    station={selectedStation}
                    train_name={selectedTrain}
                    isLoading={isLoadingArrivals}
                  />
                  <TrainArrivalsTable
                    arrivals={arrivals}
                    isLoading={isLoadingArrivals}
                  />
                </>
              )}
            </div>
          </div>
        </div>
      </main>
      <Footer />
      <div className="flex-grow"></div>
      <div className="p-4 text-gray-500 text-sm text-center">
        <a href="/imprint.txt" className="hover:text-gray-700 transition-colors mr-4">Imprint</a>
        <a href="/legal.txt" className="hover:text-gray-700 transition-colors mr-4">Legal</a>
        <a href="/privacy.txt" className="hover:text-gray-700 transition-colors">Privacy</a>
      </div>
    </div>
  );
}

export default App;
