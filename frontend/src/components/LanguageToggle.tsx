import { Listbox, Transition } from '@headlessui/react';
import { ChevronDownIcon } from '@heroicons/react/20/solid';
import { Fragment } from 'react';
import { useTranslation } from 'react-i18next';

const languages = [
  { code: 'en', label: 'EN' },
  { code: 'de', label: 'DE' }
];

export function LanguageToggle() {
  const { t, i18n } = useTranslation();

  return (
    <Listbox value={i18n.language} onChange={(lang) => i18n.changeLanguage(lang)}>
      <div className="relative">
        <Listbox.Button className="inline-flex items-center rounded-md bg-db-red-600 px-3 py-2 text-sm font-semibold text-white shadow-sm ring-1 ring-inset ring-white/10 hover:bg-db-red-500 focus:outline-none" aria-label={t('language.select')}>
          <span>{i18n.language.toUpperCase()}</span>
          <ChevronDownIcon className="ml-2 -mr-1 h-5 w-5" aria-hidden="true" />
        </Listbox.Button>
        <Transition
          as={Fragment}
          leave="transition ease-in duration-100"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <Listbox.Options className="absolute right-0 mt-1 max-h-60 w-32 overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm z-10">
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