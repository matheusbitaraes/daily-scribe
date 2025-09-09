# Development Plan: User Unsubscription Journey

## Executive Summary

This plan details the tasks required to implement the user unsubscription journey. The primary goal is to provide a straightforward and user-friendly way for subscribers to opt out of the daily digest. This will involve adding an unsubscribe link to all digest emails, creating a new backend endpoint to handle unsubscription requests, and developing a frontend confirmation page.

## Task Breakdown

### Phase 1: Backend API Development

#### Task 1: Add Unsubscribe Link to Email Template
**Type:** Backend
**Dependencies:** None

##### Description
Modify the email digest template to include a dynamically generated unsubscribe link in the footer of every email. This link will contain a unique token to identify the user.

##### Technical Details
- **File to modify:** `src/components/email_builder.py` (or wherever the email template is generated)
- **Logic:**
  - Generate a unique, secure token for each subscriber (e.g., a JWT or a simple random token stored in the database).
  - Append the token to the unsubscribe URL (e.g., `https://yourdomain.com/unsubscribe?token=...`).
  - Add the full unsubscribe link to the email footer.

##### Acceptance Criteria
- [ ] Every digest email includes a valid unsubscribe link.
- [ ] The link contains a unique and secure token.

---

#### Task 2: Implement Unsubscription Endpoint
**Type:** Backend
**Dependencies:** Task 1

##### Description
Create a new FastAPI endpoint to handle unsubscription requests. This endpoint will validate the token and update the user's subscription status in the database.

##### Technical Details
- **File to modify:** `src/api.py`
- **New endpoint:** `POST /unsubscribe`
- **Request body:** `{ "token": "user-token" }`
- **Logic:**
  - Validate the token.
  - Find the user associated with the token.
  - Update the user's `is_active` status to `false` in the `users` table.
  - Return a success response.

##### Acceptance Criteria
- [ ] Endpoint successfully deactivates a user's subscription.
- [ ] Endpoint returns an error for invalid or expired tokens.
- [ ] The user's `is_active` status is set to `false`.

---

### Phase 2: Frontend Component Development

#### Task 3: Create Unsubscription Confirmation Page
**Type:** Frontend
**Dependencies:** Task 2

##### Description
Develop a new page where users can confirm their unsubscription. This page will be the destination for the unsubscribe link in the email.

##### Technical Details
- **File to create:** `frontend/src/pages/UnsubscribePage.js`
- **Routing:** Add a new route for `/unsubscribe`.
- **Logic:**
  - Extract the token from the URL query parameters.
  - Display a confirmation message and a button to confirm the unsubscription.
  - On confirmation, send a `POST` request to the `/unsubscribe` endpoint with the token.
  - Show a final success or error message.

##### Acceptance Criteria
- [ ] The page correctly extracts the token from the URL.
- [ ] The user can confirm their unsubscription with a single click.
- [ ] The page displays a clear success message after unsubscribing.
- [ ] The page handles errors gracefully.

---

### Phase 3: Integration & Testing

#### Task 4: End-to-End Unsubscription Flow Testing
**Type:** Testing
**Dependencies:** Task 2, Task 3

##### Description
Conduct comprehensive end-to-end testing of the unsubscription process.

##### Technical Details
- **Manual testing:**
  - Click the unsubscribe link from a test email.
  - Confirm unsubscription on the confirmation page.
  - Verify that the user's status is updated in the database.
  - Ensure that the user no longer receives digest emails.
- **Automated testing:**
  - Write unit tests for the `/unsubscribe` endpoint.
  - Write unit tests for the `UnsubscribePage` component.

##### Acceptance Criteria
- [ ] All test scenarios, including error cases, pass successfully.
- [ ] The unsubscription process is reliable and user-friendly.

---

### Phase 4: Documentation & Cleanup

#### Task 5: Update API and User Documentation
**Type:** Documentation
**Dependencies:** Task 2

##### Description
Update the API documentation to include the new `/unsubscribe` endpoint and update the user guide to explain how to unsubscribe.

##### Technical Details
- **Files to modify:**
  - `docs/api-reference.md`
  - `docs/user-guide.md`
- **Content:**
  - Add details for the `POST /unsubscribe` endpoint.
  - Add a section in the user guide explaining the unsubscription process.

##### Acceptance Criteria
- [ ] All relevant documentation is updated and accurate.

## Timeline

- **Phase 1 (Backend):** 1-2 days
- **Phase 2 (Frontend):** 1-2 days
- **Phase 3 (Testing):** 1 day
- **Phase 4 (Documentation):** <1 day
- **Total Estimated Time:** 3-5 days

## Risk Assessment

- **Token Security:** Unsubscribe tokens should be handled securely to prevent unauthorized unsubscriptions.
- **User Experience:** The process should be simple and hassle-free. Avoid requiring users to log in to unsubscribe.

## Success Criteria

- A user can easily and successfully unsubscribe from the daily digest.
- The system is secure and prevents accidental or malicious unsubscriptions.
- The user receives clear confirmation that they have been unsubscribed.
