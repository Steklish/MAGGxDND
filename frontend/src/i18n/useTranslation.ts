import { useMemo, useCallback } from 'react';
import { useGameStore } from '../store/gameStore';
import { translations, SupportedLanguage, Translations } from './translations';

export const useTranslation = () => {
    const { language, setLanguage } = useGameStore();

    const currentLang: SupportedLanguage = (language === 'ru' || language === 'en') ? language : 'en';

    const t = useMemo(() => {
        return translations[currentLang] || translations.en;
    }, [currentLang]);

    const changeLanguage = useCallback((newLang: SupportedLanguage) => {
        setLanguage(newLang);
    }, [setLanguage]);

    return {
        language: currentLang,
        t,
        setLanguage: changeLanguage,
        isRu: currentLang === 'ru',
        isEn: currentLang === 'en',
    };
};
