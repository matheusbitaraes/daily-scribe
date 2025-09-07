/**
 * Source selection component
 * Allows users to select preferred news sources with search and filtering
 * 
 * @param {Array} selectedSources - Array of selected source IDs
 * @param {Array} availableSources - Array of source objects with {id, name} structure
 * @param {Function} onChange - Callback that receives array of selected source IDs
 * @param {Object} error - Form validation error object
 * @param {Function} register - React Hook Form register function
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

  // Debug logging
  React.useEffect(() => {
    console.log('SourceSelector received:');
    console.log('selectedSources:', selectedSources, 'type:', typeof selectedSources[0]);
    console.log('availableSources:', availableSources.slice(0, 3), 'id types:', availableSources.slice(0, 3).map(s => typeof s.id));
  }, [selectedSources, availableSources]);

  // Filter sources based on search term and selected filter
  const filteredSources = useMemo(() => {
    let sources = availableSources;
    
    if (searchTerm) {
      sources = sources.filter(source =>
        source.name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    if (showOnlySelected) {
      sources = sources.filter(source => 
        selectedSources.includes(source.id) || selectedSources.includes(String(source.id))
      );
    }
    
    return sources.sort((a, b) => a.name.localeCompare(b.name));
  }, [availableSources, searchTerm, showOnlySelected, selectedSources]);

  const handleSourceToggle = (source) => {
    const isSelected = selectedSources.includes(source.id) || selectedSources.includes(String(source.id));
    let newSources;
    
    if (isSelected) {
      // Remove both number and string versions to be safe
      newSources = selectedSources.filter(id => id !== source.id && id !== String(source.id));
    } else {
      newSources = [...selectedSources, source.id];
    }
    
    onChange(newSources);
  };

  const handleSelectAll = () => {
    onChange(filteredSources.map(source => source.id));
  };

  const handleClearAll = () => {
    if (showOnlySelected || searchTerm) {
      // If filtering, only clear the visible sources
      const sourcesToRemove = filteredSources.map(source => source.id);
      const newSources = selectedSources.filter(id => 
        !sourcesToRemove.includes(id) && !sourcesToRemove.includes(String(id))
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
          disabled={filteredSources.every(source => 
            selectedSources.includes(source.id) || selectedSources.includes(String(source.id))
          )}
        >
          {searchTerm || showOnlySelected ? 'Selecionar Visíveis' : 'Selecionar Todas'}
        </button>
        <button
          type="button"
          onClick={handleClearAll}
          className="btn btn-small btn-outline"
          disabled={filteredSources.every(source => 
            !selectedSources.includes(source.id) && !selectedSources.includes(String(source.id))
          )}
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
            const isSelected = selectedSources.includes(source.id) || selectedSources.includes(String(source.id));
            
            return (
              <div
                key={source.id}
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
                aria-label={`${isSelected ? 'Desmarcar' : 'Marcar'} fonte ${source.name}`}
              >
                <input
                  type="checkbox"
                  {...register('sources')}
                  value={source.id}
                  checked={isSelected}
                  onChange={() => handleSourceToggle(source)}
                  className="source-checkbox"
                  aria-label={`Fonte ${source.name}`}
                />
                
                <span className="source-name">{source.name}</span>
                
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
              ` (${filteredSources.filter(s => selectedSources.includes(s.id)).length} visível(is))`
            ) : ''}
          </span>
        )}
      </div>
    </div>
  );
};

export default SourceSelector;
