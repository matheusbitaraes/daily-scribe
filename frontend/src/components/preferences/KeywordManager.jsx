import React, { useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Alert,
  Chip,
  Stack,
  Paper,
  InputAdornment,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';

/**
 * Keyword management component
 * Allows users to add/remove keywords for content filtering
 */
const KeywordManager = ({
  keywords = [],
  onChange,
  error,
  register
}) => {
  const [newKeyword, setNewKeyword] = useState('');
  const [keywordError, setKeywordError] = useState('');
  const [confirmClearOpen, setConfirmClearOpen] = useState(false);

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
    setConfirmClearOpen(false);
    onChange([]);
  };

  // Filter suggestions to show only those not already added
  const availableSuggestions = keywordSuggestions.filter(
    suggestion => !keywords.includes(suggestion)
  );

  const isMaxReached = keywords.length >= 20;
  const canAdd = newKeyword.trim() && !isMaxReached;

  return (
    <Box>
      <Typography variant="h5" component="h3" gutterBottom>
        Palavras-chave
      </Typography>
      
      <Typography variant="body2" color="text.secondary" paragraph>
        Adicione palavras-chave para personalizar ainda mais seu conteúdo. 
        O sistema priorizará notícias que contenham essas palavras.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error.message}
        </Alert>
      )}

      {/* Add keyword input */}
      <Stack spacing={2} sx={{ mb: 3 }}>
        <Stack direction="row" spacing={1}>
          <TextField
            value={newKeyword}
            onChange={(e) => {
              setNewKeyword(e.target.value);
              setKeywordError('');
            }}
            onKeyPress={handleKeyPress}
            placeholder="Digite uma palavra-chave..."
            size="small"
            error={!!keywordError}
            helperText={keywordError}
            disabled={isMaxReached}
            inputProps={{ maxLength: 50 }}
            sx={{ flexGrow: 1 }}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <Typography variant="caption" color="text.secondary">
                    {keywords.length}/20
                  </Typography>
                </InputAdornment>
              ),
            }}
          />
          
          <Button
            onClick={handleAddKeyword}
            variant="contained"
            size="small"
            disabled={!canAdd}
          >
            Adicionar
          </Button>
        </Stack>
        
        <Typography variant="caption" color="text.secondary">
          Pressione Enter ou clique em "Adicionar"
        </Typography>
      </Stack>

      {/* Current keywords */}
      {keywords.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
            <Typography variant="h6" component="h4">
              Suas palavras-chave ({keywords.length})
            </Typography>
            <Button
              onClick={() => setConfirmClearOpen(true)}
              variant="text"
              size="small"
              color="error"
            >
              Limpar todas
            </Button>
          </Stack>
          
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              {keywords.map((keyword, index) => (
                <Chip
                  key={`${keyword}-${index}`}
                  label={keyword}
                  onDelete={() => handleRemoveKeyword(keyword)}
                  color="primary"
                  variant="filled"
                  size="small"
                />
              ))}
            </Stack>
          </Paper>
          
          {/* Hidden inputs for form registration */}
          {keywords.map((keyword, index) => (
            <input
              key={`hidden-${keyword}-${index}`}
              type="hidden"
              {...register('keywords')}
              value={keyword}
            />
          ))}
        </Box>
      )}

      {/* Keyword suggestions */}
      {availableSuggestions.length > 0 && !isMaxReached && (
        <Accordion sx={{ mb: 3 }}>
          <AccordionSummary
            aria-controls="suggestions-content"
            id="suggestions-header"
          >
            <Typography variant="h6" component="h4">
              Sugestões ({availableSuggestions.length})
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {availableSuggestions.slice(0, 20).map((suggestion) => (
                  <Chip
                    key={suggestion}
                    label={suggestion}
                    onClick={() => handleSuggestionClick(suggestion)}
                    variant="outlined"
                    size="small"
                    clickable
                  />
                ))}
              </Stack>
            </Paper>
          </AccordionDetails>
        </Accordion>
      )}

      {/* Confirmation Dialog */}
      <Dialog
        open={confirmClearOpen}
        onClose={() => setConfirmClearOpen(false)}
        aria-labelledby="confirm-clear-title"
      >
        <DialogTitle id="confirm-clear-title">
          Limpar todas as palavras-chave?
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            Tem certeza que deseja remover todas as palavras-chave? Esta ação não pode ser desfeita.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmClearOpen(false)} color="inherit">
            Cancelar
          </Button>
          <Button onClick={handleClearAll} color="error" variant="contained">
            Confirmar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default KeywordManager;