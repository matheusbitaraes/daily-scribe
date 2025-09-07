---
description: 'Description of the custom chat mode.'
tools: ['codebase', 'usages', 'vscodeAPI', 'problems', 'changes', 'testFailure', 'terminalSelection', 'terminalLastCommand', 'openSimpleBrowser', 'fetch', 'findTestFiles', 'searchResults', 'githubRepo', 'extensions', 'runTests', 'editFiles', 'runNotebooks', 'search', 'new', 'runCommands', 'runTasks', 'getPythonEnvironmentInfo', 'getPythonExecutableCommand', 'installPythonPackage', 'configurePythonEnvironment']
---
Define the purpose of this chat mode and how AI should behave: response style, available tools, focus areas, and any mode-specific instructions or constraints.

# Development Best Practices

## Python Best Practices

### Code Structure and Organization
- Follow PEP 8 style guide for Python code
- Use meaningful function and variable names
- Keep functions small and focused on a single responsibility
- Use type hints for function parameters and return values
- Organize code into logical modules and packages
- Use __init__.py files to define packagexw interfaces

### Error Handling
- Use specific exception types instead of generic Exception
- Implement proper exception handling with try/except/finally
- Log errors with appropriate context and severity levels
- Use custom exceptions for domain-specific errors
- Handle edge cases gracefully
- Avoid bare except clauses

### Functions and Classes
- Use dataclasses for simple data containers
- Implement proper __str__ and __repr__ methods
- Use @property for computed attributes
- Follow single responsibility principle for classes
- Use dependency injection for better testability
- Implement proper inheritance hierarchies

### Data Handling
- Use appropriate data structures (dict, set, list, tuple)
- Leverage list/dict comprehensions for readability
- Use generators for memory-efficient iteration
- Implement proper data validation
- Use Pydantic models for API data validation
- Handle None values explicitly

### Database and API Design
- Use SQLAlchemy or similar ORM for database operations
- Implement proper database connection pooling
- Use FastAPI best practices for API design
- Implement proper request/response models
- Use dependency injection for database sessions
- Handle database transactions properly

### Testing
- Write unit tests using pytest
- Use fixtures for test data and setup
- Mock external dependencies appropriately
- Test edge cases and error conditions
- Implement integration tests for complex workflows
- Maintain high test coverage (>80%)

### Performance
- Use appropriate data structures for performance
- Implement caching where beneficial
- Use async/await for I/O-bound operations
- Profile code to identify bottlenecks
- Optimize database queries
- Use connection pooling for external services

### Documentation
- Write clear docstrings for all public functions and classes
- Use Google or NumPy docstring format
- Document complex algorithms and business logic
- Keep README files up to date
- Document API endpoints thoroughly
- Include type information in docstrings

### Security
- Validate all user inputs
- Use parameterized queries to prevent SQL injection
- Implement proper authentication and authorization
- Sanitize data before processing
- Use environment variables for sensitive configuration
- Log security-relevant events

### Configuration and Environment
- Use environment variables for configuration
- Implement proper configuration validation
- Use different configs for dev/test/prod environments
- Keep secrets out of version control
- Use configuration files for complex settings
- Implement proper logging configuration

---

## React Best Practices

### Component Structure
- Use functional components over class components
- Keep components small and focused
- Extract reusable logic into custom hooks
- Use composition over inheritance
- Implement proper prop types with TypeScript
- Split large components into smaller, focused ones

## Hooks
- Follow the Rules of Hooks
- Use custom hooks for reusable logic
- Keep hooks focused and simple
- Use appropriate dependency arrays in useEffect
- Implement cleanup in useEffect when needed
- Avoid nested hooks

## State Management
- Use useState for local component state
- Implement useReducer for complex state logic
- Use Context API for shared state
- Keep state as close to where it's used as possible
- Avoid prop drilling through proper state management
- Use state management libraries only when necessary

## Performance
- Implement proper memoization (useMemo, useCallback)
- Use React.memo for expensive components
- Avoid unnecessary re-renders
- Implement proper lazy loading
- Use proper key props in lists
- Profile and optimize render performance

## Forms
- Use controlled components for form inputs
- Implement proper form validation
- Handle form submission states properly
- Show appropriate loading and error states
- Use form libraries for complex forms
- Implement proper accessibility for forms

## Error Handling
- Implement Error Boundaries
- Handle async errors properly
- Show user-friendly error messages
- Implement proper fallback UI
- Log errors appropriately
- Handle edge cases gracefully

## Testing
- Write unit tests for components
- Implement integration tests for complex flows
- Use React Testing Library
- Test user interactions
- Test error scenarios
- Implement proper mock data

## Accessibility
- Use semantic HTML elements
- Implement proper ARIA attributes
- Ensure keyboard navigation
- Test with screen readers
- Handle focus management
- Provide proper alt text for images

## Code Organization
- Group related components together
- Use proper file naming conventions
- Implement proper directory structure
- Keep styles close to components
- Use proper imports/exports
- Document complex component logic 


# Backend instructions
- To run the backend server locally, always call uvicorn api:app --app-dir src --reload
- If you see any improvements that can be made to the backend, please suggest them and apply only if authorized.
- If you add any new dependencies, please make sure to update the requirements.txt file accordingly.
- If you make any changes to the database schema, please ensure to create and apply the necessary migrations.



# Frontend instructions
- To run the frontend server locally, always call npm start inside the frontend folder

IMPORTANT: Always add/update documentation AND unit tests when you make changes to the codebase.