# Home Page Feature Documentation

## Overview

The Home page serves as the main landing page for Daily Scribe, replacing the simple Articles tab. It provides a comprehensive interface for browsing and filtering news articles with advanced search and filtering capabilities.

## Features

### 1. Article Display
- **Grid Layout**: Articles are displayed in a responsive grid layout
- **Article Cards**: Each article is presented in a card format with:
  - Title (linked to original article)
  - Summary (truncated to 3 lines)
  - Source name and category
  - Publication date
  - "Read Full Article" button

### 2. Advanced Filtering

#### Search
- Real-time search across article titles, summaries, and sources
- Search results update immediately as you type

#### Category Filters
- Filter articles by category (Technology, Business, Science, etc.)
- Shows article count per category
- Multiple categories can be selected

#### Source Filters
- Filter articles by news source (TechCrunch, BBC News, Reuters, etc.)
- Shows article count per source
- Multiple sources can be selected

#### Date Range Filters
- Manual date range selection with from/to date inputs
- Quick date options:
  - Today
  - Yesterday
  - Last 7 days
- Integration with available dates from the API

### 3. User Interface

#### Collapsible Sidebar
- Filter sidebar can be collapsed to save screen space
- Toggle button shows ← (collapse) or → (expand)
- Responsive design adapts on mobile devices

#### Filter Management
- Active filter counter shows number of applied filters
- "Clear All" button to reset all filters
- Individual filter tags can be removed
- Filter sections can be expanded/collapsed

#### Responsive Design
- Mobile-first responsive design
- Grid adapts to different screen sizes
- Sidebar becomes full-width on mobile
- Touch-friendly interface elements

### 4. Loading States and Error Handling
- Loading spinner while fetching data
- Error messages for failed API calls
- Empty state when no articles match filters
- Graceful fallback for missing data

## API Integration

The Home page integrates with the following backend endpoints:

- `GET /articles` - Fetch articles with filtering and pagination
- `GET /categories` - Get available categories with counts
- `GET /sources` - Get available sources with counts
- `GET /digest/available-dates` - Get dates with available articles

## Performance Features

- Pagination support (20 articles per page)
- Client-side filtering for search functionality
- Optimized API calls with proper dependency arrays
- Memory efficient with proper cleanup

## Accessibility

- Proper ARIA labels and roles
- Keyboard navigation support
- Screen reader friendly
- High contrast design
- Focus management

## Testing

Comprehensive test coverage includes:
- Component rendering tests
- Filter functionality tests
- API integration tests
- Error handling tests
- Accessibility tests
- Responsive design tests

## File Structure

```
src/components/
├── Home.js              # Main Home component
├── Home.css             # Comprehensive styling
└── tests/
    ├── Home.simple.test.js      # Basic functionality tests
    ├── Home.test.js             # Detailed unit tests
    └── Home.integration.test.js # Integration tests
```

## Future Enhancements

Potential improvements for the Home page:

1. **Advanced Search**: Full-text search with operators
2. **Sorting Options**: Sort by date, relevance, source
3. **Saved Filters**: Save and restore filter combinations
4. **Article Bookmarking**: Save articles for later reading
5. **Infinite Scroll**: Load more articles automatically
6. **Export Options**: Export filtered results
7. **Reading Time Estimation**: Show estimated reading time
8. **Article Preview**: Quick preview without leaving the page

## Technical Notes

- Uses React hooks for state management
- Implements proper error boundaries
- Follows React best practices
- CSS Grid and Flexbox for layout
- Mobile-first responsive design approach
- Performance optimized with useCallback and useMemo where needed
