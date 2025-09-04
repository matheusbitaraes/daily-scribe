# User Story: Email Digest Simulation Frontend

## Epic: Frontend Enhancement for Email Digest Preview

### Story: Email Digest Simulation and Preview Page

**As a** user of the Daily Scribe application,  
**I want** to preview and simulate the email digest that would be generated for any given date,  
**so that** I can visualize how the digest will look before it's sent via email and test different date ranges and configurations.

---

## Background & Context

The Daily Scribe application currently generates HTML email digests automatically on a daily schedule. However, there's no way for users to:
- Preview what the digest looks like before sending
- Test digest generation for historical dates
- Simulate digest content with different article sets
- Debug digest formatting and layout issues
- Validate that the categorization and clustering is working correctly

This feature will bridge the gap between the backend digest generation and user visibility, providing a web interface that mirrors the exact email content users receive.

---

## Detailed Requirements

### Functional Requirements

**FR1: Digest Simulation Interface**
- The frontend shall provide a dedicated page/route for digest simulation
- Users can select a specific date to generate a digest for
- Users can optionally filter by categories or sources before generating the digest
- The interface should show loading states during digest generation

**FR2: Digest Rendering**
- The simulated digest shall render using the exact same HTML structure and styling as the email digest
- Content shall be grouped by categories in the same order as the email version
- Article clustering shall be identical to the email version
- Related articles shall be displayed in the same nested format

**FR3: Interactive Features**
- Users can click on article links to open them in new tabs
- Users can see metadata about the digest (number of articles, categories covered, generation timestamp)

**FR4: Historical Date Support**
- Users can generate digests for any date that has articles in the database
- The system shall handle empty dates gracefully (show appropriate messaging)
- Date picker should highlight dates that have available articles

### Non-Functional Requirements

**NFR1: Performance**
- Digest simulation should complete within 3 seconds for typical data sets
- The page should be responsive and work on mobile devices
- Large digests (100+ articles) should render smoothly

**NFR2: Accuracy**
- The simulated digest must be pixel-perfect identical to the actual email digest
- All styling, fonts, and layout should match exactly
- Article ordering and clustering must be identical

**NFR3: Usability**
- The interface should be intuitive for non-technical users
- Error messages should be clear and actionable
- The feature should integrate seamlessly with the existing frontend

---

## Technical Implementation Details

### Backend API Enhancements

**New Endpoints Required:**

1. `GET /digest/simulate`
   - Query parameters: `date` (YYYY-MM-DD), `category[]` (optional), `source_id[]` (optional)
   - Returns: Complete HTML digest content for the specified date and filters
   - Uses the existing `DigestBuilder` class to ensure consistency

2. `GET /digest/available-dates`
   - Returns: Array of dates that have articles available for digest generation
   - Used to populate the date picker and highlight available dates

3. `GET /digest/metadata/{date}`
   - Returns: Metadata about articles available for the specified date
   - Includes: total article count, categories distribution, source breakdown

### Frontend Components

**New Components to Create:**

1. **DigestSimulator.js** - Main container component
   - Manages state for selected date, filters, and generated digest
   - Handles API calls and loading states
   - Coordinates between child components

2. **DigestDatePicker.js** - Date selection component
   - Calendar interface with available dates highlighted
   - Integration with available-dates API
   - Validation for date selection

3. **DigestFilters.js** - Filter configuration component
   - Category checkboxes
   - Source selection
   - Filter summary display

4. **DigestPreview.js** - Main digest display component
   - Renders the HTML digest content safely
   - Handles responsive display
   - Includes mobile/desktop toggle

5. **DigestMetadata.js** - Digest statistics component
   - Shows article count, categories, sources
   - Generation timestamp
   - Export/copy options

**Updated Components:**

6. **App.js** - Add new route for digest simulation
7. **Navigation component** - Add link to digest simulation page

### API Integration Flow

```
1. User navigates to /digest-simulator
2. Component loads available dates from API
3. User selects date and optional filters
4. Component calls /digest/simulate API
5. Generated HTML digest is displayed in preview component
6. User can interact with links, toggle views, export content
```

---

## Acceptance Criteria

### AC1: Core Functionality
- [ ] Users can access a new "Digest Simulator" page from the main navigation
- [ ] Users can select any date that has articles in the database
- [ ] The system generates and displays a digest that is visually identical to the email version
- [ ] All article links in the simulated digest are functional and open in new tabs

### AC2: Date Selection
- [ ] Date picker shows a calendar interface
- [ ] Dates with available articles are visually highlighted
- [ ] Selecting a date with no articles shows an appropriate empty state message
- [ ] The current date is pre-selected by default (if articles exist)

### AC3: Filtering Capabilities
- [ ] Users can filter articles by category before generating the digest
- [ ] Users can filter articles by source before generating the digest
- [ ] Applied filters are clearly displayed and can be easily cleared
- [ ] Filtered digests maintain the same structure and styling as unfiltered ones

### AC4: Preview Accuracy
- [ ] The simulated digest HTML is byte-for-byte identical to what would be generated for email
- [ ] All CSS styling renders correctly in the browser
- [ ] Dark mode support works correctly (if applicable)
- [ ] Mobile responsive layout matches email client rendering

### AC5: Performance & UX
- [ ] Digest generation completes within 3 seconds for typical datasets
- [ ] Loading states are shown during API calls
- [ ] Error states are handled gracefully with user-friendly messages
- [ ] The interface is intuitive and requires no documentation to use

### AC6: Metadata & Export
- [ ] Users can see summary statistics about the generated digest
- [ ] Users can copy the raw HTML to clipboard
- [ ] Users can preview the digest in mobile/desktop layouts
- [ ] Generation timestamp and parameters are displayed

---

## Future Enhancements (Out of Scope)

- **Email Testing**: Send test emails directly from the interface
- **A/B Testing**: Compare multiple digest formats side-by-side
- **Custom Templates**: Allow users to modify digest templates
- **Scheduled Previews**: Automatically generate previews for upcoming digests
- **Analytics Integration**: Track which articles are most clicked in previews

---

## Dependencies

### Technical Dependencies
- Backend: FastAPI endpoints for digest simulation
- Frontend: React Router for new page routing
- Database: Existing article and clustering data
- Existing: DigestBuilder class for HTML generation

### Team Dependencies
- Backend development for new API endpoints
- Frontend development for React components
- Testing for accuracy validation
- UX review for interface design

---

## Risks & Mitigations

### Risk 1: Performance with Large Datasets
- **Risk**: Digest generation might be slow with large numbers of articles
- **Mitigation**: Implement pagination, caching, and async generation

### Risk 2: HTML Rendering Inconsistencies
- **Risk**: Browser rendering might differ from email client rendering
- **Mitigation**: Use CSS resets and test across multiple browsers

### Risk 3: Mobile Responsiveness
- **Risk**: Complex digest layouts might not work well on mobile
- **Mitigation**: Implement responsive design patterns and test on real devices

---

## Success Metrics

- **Usage**: 80% of users try the digest simulator within first month
- **Accuracy**: Zero reported discrepancies between simulated and actual email digests
- **Performance**: 95% of digest generations complete within 3 seconds
- **Satisfaction**: Positive feedback from user testing sessions

---

## Timeline Estimate

- **Backend API Development**: 2-3 days
- **Frontend Component Development**: 3-4 days
- **Integration & Testing**: 1-2 days
- **Total Estimated Timeline**: 1 week

---

*This user story provides a comprehensive foundation for implementing email digest simulation in the Daily Scribe frontend, ensuring users can preview and validate their daily digest content before it's delivered via email.*
