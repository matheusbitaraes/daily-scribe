/**
 * Keyword management component
 * Allows users to add/remove keywords for content filtering
 */
import React, { useState } from 'react';

const KeywordManager = ({
  keywords = [],
  onChange,
  error,
  register
}) => {
  const [newKeyword, setNewKeyword] = useState('');
  const [keywordError, setKeywordError] = useState('');

  // Predefined suggestions for common keywords
  const keywordSuggestions = [
    'brasil', 'política', 'tecnologia', 'ciência', 'saúde',
    'negócios', 'finanças', 'esportes', 'entretenimento', 'clima',
    'educação', 'inovação', 'startup', 'criptomoeda',
    'inteligência artificial', 'aprendizado de máquina', 'futebol', 'basquete',
    'música', 'cinema', 'sustentabilidade', 'meio ambiente', 'viagem',
    'cultura', 'história', 'arte', 'literatura', 'design', 'fotografia',
    'moda', 'gastronomia', 'bem-estar', 'fitness', 'yoga', 'meditação',
    'psicologia', 'desenvolvimento pessoal', 'carreira', 'empreendedorismo',
  ];

  const handleAddKeyword = () => {
    const trimmedKeyword = newKeyword.trim().toLowerCase();
    
    // Validation
    if (!trimmedKeyword) {
      setKeywordError('Digite uma palavra-chave válida');
      return;
    }
    
    if (trimmedKeyword.length < 2) {
      setKeywordError('Palavra-chave deve ter pelo menos 2 caracteres');
      return;
    }
    
    if (trimmedKeyword.length > 50) {
      setKeywordError('Palavra-chave deve ter no máximo 50 caracteres');
      return;
    }
    
    if (keywords.includes(trimmedKeyword)) {
      setKeywordError('Esta palavra-chave já foi adicionada');
      return;
    }
    
    if (keywords.length >= 20) {
      setKeywordError('Máximo de 20 palavras-chave permitidas');
      return;
    }

    // Add keyword
    const newKeywords = [...keywords, trimmedKeyword];
    onChange(newKeywords);
    setNewKeyword('');
    setKeywordError('');
  };

  const handleRemoveKeyword = (keywordToRemove) => {
    const newKeywords = keywords.filter(keyword => keyword !== keywordToRemove);
    onChange(newKeywords);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddKeyword();
    }
  };

  const handleSuggestionClick = (suggestion) => {
    if (!keywords.includes(suggestion) && keywords.length < 20) {
      const newKeywords = [...keywords, suggestion];
      onChange(newKeywords);
    }
  };

  const handleClearAll = () => {
    if (window.confirm('Tem certeza que deseja remover todas as palavras-chave?')) {
      onChange([]);
    }
  };

  // Filter suggestions to show only those not already added
  const availableSuggestions = keywordSuggestions.filter(
    suggestion => !keywords.includes(suggestion)
  );

  return (
    <div className="keyword-manager">
      <div className="section-header">
        <h3>🔍 Palavras-chave</h3>
        <p className="section-description">
          Adicione palavras-chave para personalizar ainda mais seu conteúdo. 
          O sistema priorizará notícias que contenham essas palavras.
        </p>
      </div>

      {error && (
        <div className="field-error">
          {error.message}
        </div>
      )}

      {/* Add keyword input */}
      <div className="keyword-input-section">
        <div className="keyword-input-group">
          <input
            type="text"
            value={newKeyword}
            onChange={(e) => {
              setNewKeyword(e.target.value);
              setKeywordError('');
            }}
            onKeyPress={handleKeyPress}
            placeholder="Digite uma palavra-chave..."
            className={`keyword-input ${keywordError ? 'error' : ''}`}
            maxLength={50}
            aria-label="Nova palavra-chave"
            disabled={keywords.length >= 20}
          />
          <button
            type="button"
            onClick={handleAddKeyword}
            className="btn btn-primary btn-small"
            disabled={!newKeyword.trim() || keywords.length >= 20}
          >
            Adicionar
          </button>
        </div>
        
        {keywordError && (
          <div className="field-error">
            {keywordError}
          </div>
        )}
        
        <div className="keyword-input-help">
          <small>
            {keywords.length}/20 palavras-chave • 
            Pressione Enter ou clique em "Adicionar"
          </small>
        </div>
      </div>

      {/* Current keywords */}
      {keywords.length > 0 && (
        <div className="current-keywords">
          <div className="keywords-header">
            <h4>Suas palavras-chave ({keywords.length})</h4>
            <button
              type="button"
              onClick={handleClearAll}
              className="btn btn-small btn-text"
            >
              Limpar todas
            </button>
          </div>
          
          <div className="keyword-tags">
            {keywords.map((keyword, index) => (
              <div key={`${keyword}-${index}`} className="keyword-tag">
                <span className="keyword-text">{keyword}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveKeyword(keyword)}
                  className="keyword-remove"
                  aria-label={`Remover palavra-chave ${keyword}`}
                >
                  ✕
                </button>
                <input
                  type="hidden"
                  {...register('keywords')}
                  value={keyword}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Keyword suggestions */}
      {availableSuggestions.length > 0 && keywords.length < 20 && (
        <div className="keyword-suggestions">
          <h4>Sugestões populares</h4>
          <div className="suggestion-tags">
            {availableSuggestions.slice(0, 10).map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => handleSuggestionClick(suggestion)}
                className="suggestion-tag"
                aria-label={`Adicionar palavra-chave sugerida ${suggestion}`}
              >
                + {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Summary */}
      <div className="selection-summary">
        {keywords.length === 0 ? (
          <span className="summary-text summary-empty">
            Nenhuma palavra-chave adicionada. O sistema usará as configurações padrão.
          </span>
        ) : (
          <span className="summary-text">
            {keywords.length} palavra(s)-chave ativa(s): {keywords.join(', ')}
          </span>
        )}
      </div>
    </div>
  );
};

export default KeywordManager;
