import { Listbox, Transition } from '@headlessui/react';
import { ChevronDownIcon } from '@heroicons/react/20/solid';
import { Fragment } from 'react';
import { useTranslation } from 'react-i18next';

const languages = [
  { code: 'en', label: 'EN' },
  { code: 'de', label: 'DE' }
];

interface LanguageToggleProps {
  className?: string;
}

export function LanguageToggle({ className = '' }: LanguageToggleProps) {
  const { t, i18n } = useTranslation();

  return (
    <Listbox value={i18n.language} onChange={(lang) => i18n.changeLanguage(lang)}>
      <div className={`relative ${className}`}>
        <Listbox.Button 
          className="inline-flex w-full items-center justify-between rounded-md px-3 py-2 text-sm font-semibold shadow-sm ring-1 ring-inset md:bg-white/10 md:text-white md:ring-white/10 md:hover:bg-white/20 bg-white text-gray-900 ring-gray-300 hover:bg-gray-50 focus:outline-none" 
          aria-label={t('language.select')}
        >
          <span>{i18n.language.toUpperCase()}</span>
          <ChevronDownIcon className="ml-2 -mr-1 h-5 w-5" aria-hidden="true" />
        </Listbox.Button>
        <Transition
          as={Fragment}
          leave="transition ease-in duration-100"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <Listbox.Options className="absolute right-0 z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
            {languages.map((lang) => (
              <Listbox.Option
                key={lang.code}
                value={lang.code}
                className={({ active }) =>
                  `relative cursor-default select-none py-2 px-4 ${
                    active ? 'bg-db-red-600 text-white' : 'text-gray-900'
                  }`
                }
              >
                {({ selected }) => (
                  <span className={`block truncate ${selected ? 'font-medium' : 'font-normal'}`}>
                    {t(`language.${lang.code}`)}
                  </span>
                )}
              </Listbox.Option>
            ))}
          </Listbox.Options>
        </Transition>
      </div>
    </Listbox>
  );
} 