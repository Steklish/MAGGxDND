import React from 'react';
import { useTranslation } from '../../i18n/useTranslation';
import { Tooltip } from './Tooltip';
import './LanguageSelector.css';

interface LanguageSelectorProps {
    className?: string;
    variant?: 'compact' | 'badge' | 'full';
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({
    className = '',
    variant = 'compact',
}) => {
    const { language, setLanguage, t } = useTranslation();

    return (
        <div className={`global-language-selector variant-${variant} ${className}`} data-testid="global-language-selector">
            <Tooltip content={t.languageSelector.tooltip} position="bottom">
                <div className="language-toggle-track" role="group" aria-label={t.languageSelector.title}>
                    <button
                        type="button"
                        className={`lang-pill ${language === 'ru' ? 'active' : ''}`}
                        onClick={() => setLanguage('ru')}
                        title={t.languageSelector.ruLabel}
                        aria-pressed={language === 'ru'}
                    >
                        <span className="lang-flag">🇷🇺</span>
                        <span className="lang-code">RU</span>
                    </button>
                    <button
                        type="button"
                        className={`lang-pill ${language === 'en' ? 'active' : ''}`}
                        onClick={() => setLanguage('en')}
                        title={t.languageSelector.enLabel}
                        aria-pressed={language === 'en'}
                    >
                        <span className="lang-flag">🇬🇧</span>
                        <span className="lang-code">EN</span>
                    </button>
                </div>
            </Tooltip>
        </div>
    );
};
