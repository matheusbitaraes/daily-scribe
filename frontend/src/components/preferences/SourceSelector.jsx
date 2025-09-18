import React, { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  TextField,
  FormControlLabel,
  Checkbox,
  Button,
  Alert,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  InputAdornment,
  IconButton,
  Paper
} from '@mui/material';

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

  const isAllSelected = filteredSources.every(source => 
    selectedSources.includes(source.id) || selectedSources.includes(String(source.id))
  );

  const isNoneSelected = filteredSources.every(source => 
    !selectedSources.includes(source.id) && !selectedSources.includes(String(source.id))
  );

  return (
    <Box>
      <Typography variant="h5" component="h3" gutterBottom>
        Fontes de Notícias
      </Typography>
      
      <Typography variant="body2" color="text.secondary" paragraph>
        Selecione suas fontes de notícias preferidas. Se nenhuma for selecionada, 
        você receberá notícias de todas as fontes disponíveis.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error.message}
        </Alert>
      )}

      {/* Search and filters */}
      <Stack spacing={2} sx={{ mb: 2 }}>
        <TextField
          placeholder="Buscar fontes..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          size="small"
          InputProps={{
            // startAdornment: (
            //   <InputAdornment position="start">
            //     <SearchIcon color="action" />
            //   </InputAdornment>
            // ),
            endAdornment: searchTerm && (
              <InputAdornment position="end">
                <IconButton
                  onClick={() => setSearchTerm('')}
                  edge="end"
                  size="small"
                  aria-label="Limpar busca"
                >
                  {/* <ClearIcon /> */}
                </IconButton>
              </InputAdornment>
            ),
          }}
          aria-label="Buscar fontes de notícias"
        />

        <FormControlLabel
          control={
            <Checkbox
              checked={showOnlySelected}
              onChange={(e) => setShowOnlySelected(e.target.checked)}
              size="small"
            />
          }
          label={
            <Typography variant="body2">
              Mostrar apenas selecionadas ({selectedSources.length})
            </Typography>
          }
        />
      </Stack>

      {/* Action buttons */}
      <Stack direction="row" spacing={1} sx={{ mb: 2 }} flexWrap="wrap">
        {/* <Button
          onClick={handleSelectAll}
          variant="outlined"
          size="small"
          disabled={isAllSelected}
        >
          {searchTerm || showOnlySelected ? 'Selecionar Visíveis' : 'Selecionar Todas'}
        </Button> */}
        
        <Button
          onClick={handleClearAll}
          variant="outlined"
          size="small"
          disabled={isNoneSelected}
        >
          {searchTerm || showOnlySelected ? 'Limpar Visíveis' : 'Limpar Todas'}
        </Button>
        
        {(searchTerm || showOnlySelected) && (
          <Button
            onClick={handleClearSearch}
            variant="text"
            size="small"
          >
            Limpar Filtros
          </Button>
        )}
      </Stack>

      {/* Sources list */}
      <Paper variant="outlined" sx={{ maxHeight: 400, overflow: 'auto', mb: 2 }}>
        {filteredSources.length === 0 ? (
          <Box p={3} textAlign="center">
            <Typography variant="body2" color="text.secondary">
              {searchTerm ? (
                <>Nenhuma fonte encontrada para "{searchTerm}"</>
              ) : showOnlySelected ? (
                'Nenhuma fonte selecionada'
              ) : (
                'Nenhuma fonte disponível'
              )}
            </Typography>
          </Box>
        ) : (
          <List dense>
            {filteredSources.map((source) => {
              const isSelected = selectedSources.includes(source.id) || selectedSources.includes(String(source.id));
              
              return (
                <ListItem
                  key={source.id}
                  disablePadding
                >
                  <ListItemButton
                    onClick={() => handleSourceToggle(source)}
                    selected={isSelected}
                    sx={{
                      '&.Mui-selected': {
                        bgcolor: 'primary.50',
                        '&:hover': {
                          bgcolor: 'primary.100',
                        },
                      },
                    }}
                  >
                    <ListItemIcon>
                      <Checkbox
                        {...register('sources')}
                        value={source.id}
                        checked={isSelected}
                        tabIndex={-1}
                        disableRipple
                        inputProps={{ 'aria-labelledby': `source-${source.id}` }}
                      />
                    </ListItemIcon>
                    
                    <ListItemText
                      id={`source-${source.id}`}
                      primary={source.name}
                      primaryTypographyProps={{
                        variant: 'body2',
                        fontWeight: isSelected ? 500 : 400,
                      }}
                    />
                  </ListItemButton>
                </ListItem>
              );
            })}
          </List>
        )}
      </Paper>

      {/* Selection summary */}
      <Box>
        {selectedSources.length === 0 ? (
          <Alert severity="info" variant="outlined">
            <Typography variant="body2">
              Nenhuma fonte selecionada. <strong>Você receberá notícias de todas as fontes.</strong>
            </Typography>
          </Alert>
        ) : (
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {selectedSources.length} fonte(s) selecionada(s)
              {(searchTerm || showOnlySelected) && (
                <> ({filteredSources.filter(s => selectedSources.includes(s.id) || selectedSources.includes(String(s.id))).length} visível(is))</>
              )}
            </Typography>
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default SourceSelector;