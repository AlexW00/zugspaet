import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../api/client';

export function Footer() {
  const { t } = useTranslation();
  const [last_import, setLastImport] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLastImport = async () => {
      try {
        const data = await api.getLastImport();
        setLastImport(data.last_import);
      } catch {
        setError(t('errors.loadLastImport'));
      }
    };
    fetchLastImport();
  }, [t]);

  if (error) return null; // Don't show footer if there's an error
  if (!last_import) return null; // Don't show footer if there's no data

  const date = new Date(last_import);
  const formattedDate = new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short'
  }).format(date);

  return (
    <footer className="bg-gray-50 py-3 text-center text-sm text-gray-500">
      {t('footer.last_import', { date: formattedDate })}
    </footer>
  );
} 