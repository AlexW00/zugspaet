const BERLIN_TIME_ZONE = 'Europe/Berlin';

function getDateParts(value: string | Date) {
  const date = typeof value === 'string' ? new Date(value) : value;
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: BERLIN_TIME_ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(date);

  return {
    year: parts.find(part => part.type === 'year')?.value ?? '0000',
    month: parts.find(part => part.type === 'month')?.value ?? '00',
    day: parts.find(part => part.type === 'day')?.value ?? '00',
  };
}

export function getBerlinDateKey(value: string | Date) {
  const { year, month, day } = getDateParts(value);
  return `${year}-${month}-${day}`;
}

export function formatBerlinDateTime(value: string | Date, locale = 'de-DE') {
  const date = typeof value === 'string' ? new Date(value) : value;
  return new Intl.DateTimeFormat(locale, {
    timeZone: BERLIN_TIME_ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

export function formatBerlinDate(value: string | Date, locale = 'de-DE') {
  const date = typeof value === 'string' ? new Date(value) : value;
  return new Intl.DateTimeFormat(locale, {
    timeZone: BERLIN_TIME_ZONE,
    month: 'numeric',
    day: 'numeric',
  }).format(date).replace(/\.$/, '');
}

export function formatBerlinTime(value: string | Date, locale = 'de-DE') {
  const date = typeof value === 'string' ? new Date(value) : value;
  return new Intl.DateTimeFormat(locale, {
    timeZone: BERLIN_TIME_ZONE,
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

export { BERLIN_TIME_ZONE };
