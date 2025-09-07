# Frontend Development Guide

This guide covers the React-based frontend application for Daily Scribe, including component architecture, development setup, and deployment procedures.

## Overview

The Daily Scribe frontend is a React single-page application (SPA) that provides a web interface for digest simulation, user preference management, and article browsing.

### Technology Stack
- **React 19.1.1** - Component-based UI library
- **React Router 7.8.2** - Client-side routing
- **Axios 0.21.1** - HTTP client for API communication
- **React Hook Form 7.62.0** - Form handling and validation
- **DOMPurify 3.2.6** - HTML sanitization for security
- **CSS Modules** - Scoped styling

### Project Structure
```
frontend/
├── public/                 # Static assets
│   ├── index.html         # HTML template
│   └── favicon.ico        # Site icon
├── src/
│   ├── components/        # React components
│   │   ├── ui/           # Reusable UI components
│   │   ├── preferences/  # Preference management
│   │   └── errors/       # Error handling components
│   ├── utils/            # Utility functions
│   │   ├── tokenValidator.js  # Token validation
│   │   └── performance.js     # Performance utilities
│   ├── App.js            # Main application component
│   ├── App.css           # Global styles
│   └── index.js          # Application entry point
├── package.json          # Dependencies and scripts
└── README.md            # Frontend-specific documentation
```

## Core Components

### 1. DigestSimulator (`/digest-simulator`)
**Purpose:** Main interface for generating and previewing email digests

**Features:**
- Date selection with availability checking
- User email input with validation
- Real-time digest generation and preview
- Filter options (categories, sources)
- Export and sharing capabilities

**Key Files:**
- `DigestSimulator.js` - Main component logic
- `DigestDatePicker.js` - Date selection interface
- `DigestPreview.js` - HTML digest rendering
- `DigestFilters.js` - Category and source filtering

### 2. PreferencePage (`/preferences/:token`)
**Purpose:** User preference management interface

**Features:**
- Token-based authentication
- Source enable/disable toggles
- Category preferences
- Keyword management
- Real-time preference updates

**Key Files:**
- `PreferencePage.js` - Main preference interface
- `CategorySelector.jsx` - Category selection component
- `PreferenceForm.jsx` - Form handling and validation

### 3. Navigation
**Purpose:** Application routing and navigation

**Features:**
- Responsive navigation menu
- Active route highlighting
- Mobile-friendly design
- Breadcrumb support

## Development Setup

### Prerequisites
- Node.js 18+ 
- npm or yarn package manager
- Access to Daily Scribe backend API

### Installation
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

### Environment Configuration
Create `.env` file in frontend directory:
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_VERSION=1.0.0
```

### Development Scripts
```bash
npm start          # Start development server (port 3000)
npm run build      # Build production bundle
npm test           # Run test suite
npm run eject      # Eject from Create React App (irreversible)
```

## Component Architecture

### State Management
The application uses React's built-in state management:
- `useState` for local component state
- `useEffect` for side effects and API calls
- `useCallback` for performance optimization
- Context API for shared state (when needed)

### API Integration
All API calls are centralized using Axios:
```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Example API call with error handling
const loadDigest = async (email, date) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/digest/simulate`, {
      params: { user_email: email, date }
    });
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to load digest');
  }
};
```

### Error Handling
Comprehensive error handling throughout the application:
- Network error handling with retry logic
- User-friendly error messages
- Fallback UI components
- Error boundary components for crash protection

### Performance Optimization
- Request deduplication to prevent duplicate API calls
- Debounced input handling for search and filters
- Lazy loading for non-critical components
- Memoization for expensive computations

## Authentication Flow

### Token-Based Authentication
1. User receives email with secure token link
2. Frontend validates token format client-side
3. Backend validates token and returns user data
4. User can manage preferences while token is valid
5. Token expires after usage limit or time limit

### Token Validation
```javascript
// Client-side token format validation
export function validateTokenFormat(token) {
  if (!token || typeof token !== 'string') {
    return { isValid: false, error: 'MISSING_TOKEN' };
  }
  
  // Check JWT format (3 parts separated by dots)
  const parts = token.split('.');
  if (parts.length !== 3) {
    return { isValid: false, error: 'INVALID_FORMAT' };
  }
  
  return { isValid: true };
}
```

## Styling Guidelines

### CSS Organization
- Component-specific CSS files alongside JS files
- Global styles in `App.css`
- CSS custom properties for theming
- Responsive design with mobile-first approach

### Color Scheme
```css
:root {
  --primary-color: #2563eb;
  --secondary-color: #64748b;
  --success-color: #059669;
  --warning-color: #d97706;
  --error-color: #dc2626;
  --background-color: #f8fafc;
  --text-color: #1e293b;
  --border-color: #e2e8f0;
}
```

### Responsive Breakpoints
```css
/* Mobile first approach */
.component {
  /* Mobile styles (default) */
}

@media (min-width: 768px) {
  /* Tablet styles */
}

@media (min-width: 1024px) {
  /* Desktop styles */
}
```

## Testing Strategy

### Unit Testing
- Component rendering tests
- User interaction testing
- API integration testing
- Utility function testing

### Integration Testing
- End-to-end user workflows
- API integration testing
- Cross-browser compatibility
- Mobile responsiveness testing

### Test Examples
```javascript
// Component test example
import { render, screen, fireEvent } from '@testing-library/react';
import DigestSimulator from './DigestSimulator';

test('renders digest simulator with email input', () => {
  render(<DigestSimulator />);
  const emailInput = screen.getByLabelText(/email/i);
  expect(emailInput).toBeInTheDocument();
});

test('generates digest when form is submitted', async () => {
  render(<DigestSimulator />);
  // Test implementation...
});
```

## Build and Deployment

### Production Build
```bash
# Create production build
npm run build

# Build output is in build/ directory
ls build/
# static/   # CSS, JS, and media files
# index.html  # Main HTML file
```

### Docker Integration
The frontend is built as part of the main Docker build process:
```dockerfile
# Frontend build stage
FROM node:18-alpine as frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci --only=production && npm cache clean --force
COPY frontend/ ./
RUN npm run build

# Production stage copies built files
COPY --from=frontend-builder /frontend/build /app/frontend/build
```

### Static File Serving
The built frontend is served by FastAPI as static files:
```python
# In src/api.py
from fastapi.staticfiles import StaticFiles

# Mount static files
app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")

# Serve index.html for all non-API routes
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    return FileResponse("frontend/build/index.html")
```

## Troubleshooting

### Common Issues

#### "API calls failing"
- Check `REACT_APP_API_URL` environment variable
- Verify backend server is running
- Check browser network tab for CORS issues
- Validate API endpoint URLs

#### "Token validation errors"
- Ensure token format is correct (JWT with 3 parts)
- Check token hasn't expired
- Verify token was generated correctly by backend

#### "Build failures"
- Clear node_modules and reinstall: `rm -rf node_modules package-lock.json && npm install`
- Check Node.js version compatibility
- Review build errors for missing dependencies

#### "Routing issues in production"
- Ensure web server is configured for SPA routing
- Check that all routes fall back to index.html
- Verify base URL configuration

### Development Tips

1. **Hot Reloading:** Development server supports hot reloading for instant updates
2. **Redux DevTools:** Browser extension available for state debugging
3. **React DevTools:** Browser extension for component inspection
4. **Network Tab:** Use browser dev tools to monitor API calls
5. **Console Logs:** Strategic logging for debugging component lifecycle

### Performance Monitoring

Monitor frontend performance using:
- Lighthouse audits for overall performance
- React DevTools Profiler for component performance
- Network tab for API call performance
- Bundle analyzer for build size optimization

```bash
# Analyze bundle size
npx webpack-bundle-analyzer build/static/js/*.js
```

## Contributing

### Code Style
- Use functional components with hooks
- Follow ESLint configuration
- Use meaningful component and variable names
- Add comments for complex logic
- Keep components small and focused

### Pull Request Process
1. Create feature branch from main
2. Implement changes with tests
3. Update documentation if needed
4. Submit PR with clear description
5. Address review feedback

### Git Commit Messages
```
feat: add digest filtering by category
fix: resolve token validation edge case
docs: update API integration examples
refactor: simplify preference form logic
```

---

This guide should be updated as the frontend evolves. For questions or issues, refer to the main project README or create an issue in the repository.
