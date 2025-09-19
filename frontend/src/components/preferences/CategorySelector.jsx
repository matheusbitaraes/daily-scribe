import {
  Box,
  Typography,
  Grid,
  Checkbox,
  FormControlLabel,
  Alert,
  Chip,
  Stack,
  Paper
} from '@mui/material';
import { CATEGORY_TRANSLATIONS } from '../../utils/categories';

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

  return (
    <Box>
      <Typography variant="h5" component="h3" gutterBottom>
        Categorias de Notícias
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error.message}
        </Alert>
      )}

      <Grid container spacing={2} sx={{ mb: 3 }} justifyContent="space-between">
        {availableCategories.map((category) => {
          const isSelected = selectedCategories.includes(category);
          const translatedName = CATEGORY_TRANSLATIONS[category] || category;
          
          return (
            <Grid item xs={12} sm={6} md={4} key={category}>
              <Paper 
                variant={isSelected ? "elevation" : "outlined"}
                sx={{
                  cursor: 'pointer',
                  transition: 'all 0.2s ease-in-out',
                  bgcolor: isSelected ? 'primary.50' : 'background.paper',
                  borderColor: isSelected ? 'primary.main' : 'divider',
                  borderRadius: 10,
                  '&:hover': {
                    boxShadow: 2,
                    transform: 'translateY(-1px)'
                  },
                }}
                onClick={() => handleCategoryToggle(category)}
              >
                <Box py={0} px={2} display="flex" alignItems="center" justifyContent="space-between">
                  <FormControlLabel
                    control={
                      <Checkbox
                        {...register('categories')}
                        value={category}
                        checked={isSelected}
                        color="primary"
                      />
                    }
                    label={
                      <Typography variant="body2" fontWeight={isSelected ? 500 : 400}>
                        {translatedName}
                      </Typography>
                    }
                    onClick={(e) => e.preventDefault()}
                    cursor="pointer"
                    sx={{ m: 0, flexGrow: 1 }}
                  />
                </Box>
              </Paper>
            </Grid>
          );
        })}
      </Grid>

      <Box>
        {selectedCategories.length === 0 ? (
          <Alert severity="info" variant="outlined">
            <Typography variant="body2">
              Nenhuma categoria selecionada. <strong>Você receberá notícias de todas as categorias.</strong>
            </Typography>
          </Alert>
        ) : (
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {selectedCategories.length} categoria(s) selecionada(s):
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              {selectedCategories.map((category) => (
                <Chip
                  key={category}
                  label={CATEGORY_TRANSLATIONS[category] || category}
                  color="primary"
                  variant="filled"
                  size="small"
                  onDelete={() => handleCategoryToggle(category)}
                />
              ))}
            </Stack>
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default CategorySelector;