/**
 * Source selection component
 * Allows users to select preferred news sources with search and filtering
 */
import React, { useState, useMemo } from 'react';

const SourceSelector = ({
  selectedSources = [],
  availableSources = [],
  onChange,
  error,
  register
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [showOnlySelected, setShowOnlySelected] = useState(false);

  // Filter sources based on search term and selected filter
  const filteredSources = useMemo(() => {
    let sources = availableSources;
    
    if (searchTerm) {
      sources = sources.filter(source =>
        source.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    if (showOnlySelected) {
      sources = sources.filter(source => 
        selectedSources.includes(source)
      );
    }
    
    return sources.sort();
  }, [availableSources, searchTerm, showOnlySelected, selectedSources]);

  const handleSourceToggle = (source) => {
    const isSelected = selectedSources.includes(source);
    let newSources;
    
    if (isSelected) {
      newSources = selectedSources.filter(src => src !== source);
    } else {
      newSources = [...selectedSources, source];
    }
    
    onChange(newSources);
  };

  const handleSelectAll = () => {
    onChange(filteredSources);
  };

  const handleClearAll = () => {
    if (showOnlySelected || searchTerm) {
      // If filtering, only clear the visible sources
      const sourcesToRemove = filteredSources;
      const newSources = selectedSources.filter(source => 
        !sourcesToRemove.includes(source)
      );
      onChange(newSources);
    } else {
      // If not filtering, clear all
      onChange([]);
    }
  };

  const handleClearSearch = () => {
    setSearchTerm('');
    setShowOnlySelected(false);
  };

  return (
    <div className="source-selector">
      <div className="section-header">
        <h3>📡 Fontes de Notícias</h3>
        <p className="section-description">
          Selecione suas fontes de notícias preferidas. Se nenhuma for selecionada, 
          você receberá notícias de todas as fontes disponíveis.
        </p>
      </div>

      {error && (
        <div className="field-error">
          {error.message}
        </div>
      )}

      {/* Search and filters */}
      <div className="source-controls">
        <div className="search-box">
          <input
            type="text"
            placeholder="Buscar fontes..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
            aria-label="Buscar fontes de notícias"
          />
          {searchTerm && (
            <button
              type="button"
              onClick={() => setSearchTerm('')}
              className="search-clear"
              aria-label="Limpar busca"
            >
              ✕
            </button>
          )}
        </div>

        <div className="filter-controls">
          <label className="filter-checkbox">
            <input
              type="checkbox"
              checked={showOnlySelected}
              onChange={(e) => setShowOnlySelected(e.target.checked)}
            />
            Mostrar apenas selecionadas ({selectedSources.length})
          </label>
        </div>
      </div>

      {/* Action buttons */}
      <div className="section-actions">
        <button
          type="button"
          onClick={handleSelectAll}
          className="btn btn-small btn-outline"
          disabled={filteredSources.every(source => selectedSources.includes(source))}
        >
          {searchTerm || showOnlySelected ? 'Selecionar Visíveis' : 'Selecionar Todas'}
        </button>
        <button
          type="button"
          onClick={handleClearAll}
          className="btn btn-small btn-outline"
          disabled={filteredSources.every(source => !selectedSources.includes(source))}
        >
          {searchTerm || showOnlySelected ? 'Limpar Visíveis' : 'Limpar Todas'}
        </button>
        {(searchTerm || showOnlySelected) && (
          <button
            type="button"
            onClick={handleClearSearch}
            className="btn btn-small btn-text"
          >
            Limpar Filtros
          </button>
        )}
      </div>

      {/* Sources list */}
      <div className="source-list">
        {filteredSources.length === 0 ? (
          <div className="empty-state">
            {searchTerm ? (
              <p>Nenhuma fonte encontrada para "{searchTerm}"</p>
            ) : showOnlySelected ? (
              <p>Nenhuma fonte selecionada</p>
            ) : (
              <p>Nenhuma fonte disponível</p>
            )}
          </div>
        ) : (
          filteredSources.map((source) => {
            const isSelected = selectedSources.includes(source);
            
            return (
              <div
                key={source}
                className={`source-item ${isSelected ? 'selected' : ''}`}
                onClick={() => handleSourceToggle(source)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    handleSourceToggle(source);
                  }
                }}
                aria-pressed={isSelected}
                aria-label={`${isSelected ? 'Desmarcar' : 'Marcar'} fonte ${source}`}
              >
                <input
                  type="checkbox"
                  {...register('sources')}
                  value={source}
                  checked={isSelected}
                  onChange={() => handleSourceToggle(source)}
                  className="source-checkbox"
                  aria-label={`Fonte ${source}`}
                />
                
                <span className="source-name">{source}</span>
                
                {isSelected && (
                  <span className="source-checkmark">✓</span>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Selection summary */}
      <div className="selection-summary">
        {selectedSources.length === 0 ? (
          <span className="summary-text summary-empty">
            Nenhuma fonte selecionada. Você receberá notícias de todas as fontes.
          </span>
        ) : (
          <span className="summary-text">
            {selectedSources.length} fonte(s) selecionada(s)
            {searchTerm || showOnlySelected ? (
              ` (${filteredSources.filter(s => selectedSources.includes(s)).length} visível(is))`
            ) : ''}
          </span>
        )}
      </div>
    </div>
  );
};

export default SourceSelector;
