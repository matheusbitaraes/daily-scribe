/**
 * Category selection component
 * Allows users to select/deselect news categories with visual feedback
 */

const CategorySelector = ({
  selectedCategories = [],
  availableCategories = [],
  onChange,
  error,
  register
}) => {
  // Category Portuguese translations
  const categoryTranslations = {
    'Politics': 'Política',
    'Technology': 'Tecnologia',
    'Science and Health': 'Saúde e Ciência',
    'Business': 'Negócios',
    'Entertainment': 'Entretenimento',
    'Sports': 'Esportes',
    'Other': 'Outros'
  };

  const handleCategoryToggle = (category) => {
    const isSelected = selectedCategories.includes(category);
    let newCategories;
    
    if (isSelected) {
      newCategories = selectedCategories.filter(cat => cat !== category);
    } else {
      newCategories = [...selectedCategories, category];
    }
    
    onChange(newCategories);
  };

  const handleSelectAll = () => {
    onChange(availableCategories);
  };

  const handleClearAll = () => {
    onChange([]);
  };

  return (
    <div className="category-selector">
      <div className="section-header">
        <h3>📂 Categorias de Notícias</h3>
      </div>

      {error && (
        <div className="field-error">
          {error.message}
        </div>
      )}

      {/* <div className="section-actions">
        <button
          type="button"
          onClick={handleSelectAll}
          className="btn btn-small btn-outline"
          disabled={selectedCategories.length === availableCategories.length}
        >
          Selecionar Todas
        </button>
        <button
          type="button"
          onClick={handleClearAll}
          className="btn btn-small btn-outline"
          disabled={selectedCategories.length === 0}
        >
          Limpar Seleção
        </button>
      </div> */}

      <div className="category-grid">
        {availableCategories.map((category) => {
          const isSelected = selectedCategories.includes(category);
          const translatedName = categoryTranslations[category] || category;
          
          return (
            <div
              key={category}
              className={`category-card ${isSelected ? 'selected' : ''}`}
              onClick={() => handleCategoryToggle(category)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleCategoryToggle(category);
                }
              }}
              aria-pressed={isSelected}
              aria-label={`${isSelected ? 'Desmarcar' : 'Marcar'} categoria ${translatedName}`}
            >
              <input
                type="checkbox"
                {...register('categories')}
                value={category}
                checked={isSelected}
                onChange={() => handleCategoryToggle(category)}
                className="category-checkbox"
                aria-label={`Categoria ${translatedName}`}
              />
              
              <div className="category-content">
                <span className="category-name">{translatedName}</span>
              </div>
              
              {isSelected && (
                <div className="category-checkmark">✓</div>
              )}
            </div>
          );
        })}
      </div>

      <div className="selection-summary">
        {selectedCategories.length === 0 ? (
          <span className="summary-text summary-empty">
            Nenhuma categoria selecionada. Você receberá notícias de todas as categorias.
          </span>
        ) : (
          <span className="summary-text">
            {selectedCategories.length} categoria(s) selecionada(s): {' '}
            {selectedCategories
              .map(cat => categoryTranslations[cat] || cat)
              .join(', ')}
          </span>
        )}
      </div>
    </div>
  );
};

export default CategorySelector;
