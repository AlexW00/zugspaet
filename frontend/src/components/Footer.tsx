import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../api/client';

export function Footer() {
  const { t } = useTranslation();
  const [lastImport, setLastImport] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLastImport = async () => {
      try {
        const data = await api.getLastImport();
        setLastImport(data.lastImport);
      } catch {
        setError(t('errors.loadLastImport'));
      }
    };
    fetchLastImport();
  }, [t]);

  if (error) return null; // Don't show footer if there's an error
  if (!lastImport) return null; // Don't show footer if there's no data

  const date = new Date(lastImport);
  const formattedDate = new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short'
  }).format(date);

  return (
    <footer className="bg-gray-50 py-3 text-center text-sm text-gray-500">
      {t('footer.lastImport', { date: formattedDate })}
    </footer>
  );
} 