# Development Plan: User Subscription Journey

## Executive Summary

This plan outlines the tasks required to implement the user subscription journey. The goal is to create a seamless experience for new users to subscribe to the Daily Scribe newsletter via a web interface. The implementation will involve creating new backend endpoints for handling subscription requests and email verification, and developing new frontend components for the subscription form and confirmation pages.

## Task Breakdown

### Phase 1: Backend API Development

#### Task 1: Create Database Migrations for Subscriptions
**Type:** Backend
**Dependencies:** None

##### Description
Create a new database migration to add tables for managing user subscriptions and verification tokens. This will include a `pending_subscriptions` table to store temporary subscription requests and a `users` table to store verified subscribers.

##### Technical Details
- **Files to create/modify:** `src/database/migrations/005_create_subscription_tables.py`
- **`pending_subscriptions` table schema:**
  - `id`: Primary Key
  - `email`: User's email address
  - `verification_token`: Secure token for email verification
  - `expires_at`: Token expiration timestamp
- **`users` table schema:**
  - `id`: Primary Key
  - `email`: User's email address
  - `subscribed_at`: Timestamp of subscription
  - `is_active`: Boolean to indicate subscription status

##### Acceptance Criteria
- [ ] Migration script runs successfully.
- [ ] `pending_subscriptions` and `users` tables are created with the correct schema.
- [ ] Relationships between tables are correctly defined.

---

#### Task 2: Implement Subscription Request Endpoint
**Type:** Backend
**Dependencies:** Task 1

##### Description
Create a new FastAPI endpoint to handle new subscription requests. This endpoint will generate a verification token, store the request in the `pending_subscriptions` table, and send a verification email to the user.

##### Technical Details
- **File to modify:** `src/api.py`
- **New endpoint:** `POST /subscribe`
- **Request body:** `{ "email": "user@example.com" }`
- **Logic:**
  - Validate the email address format.
  - Check if the email is already subscribed or pending verification.
  - Generate a unique, secure verification token.
  - Store the email and token in the `pending_subscriptions` table.
  - Send a verification email with a link containing the token.

##### Acceptance Criteria
- [ ] Endpoint returns `200 OK` for valid requests.
- [ ] Endpoint returns `400 Bad Request` for invalid email formats.
- [ ] Endpoint returns `409 Conflict` if the email is already subscribed.
- [ ] A new record is created in the `pending_subscriptions` table.
- [ ] A verification email is sent to the user.

---

#### Task 3: Implement Email Verification Endpoint
**Type:** Backend
**Dependencies:** Task 2

##### Description
Create an endpoint to handle email verification. This endpoint will validate the verification token, move the user from the pending table to the `users` table, and mark them as an active subscriber.

##### Technical Details
- **File to modify:** `src/api.py`
- **New endpoint:** `GET /verify-email`
- **Query parameters:** `token`
- **Logic:**
  - Find the token in the `pending_subscriptions` table.
  - If the token is valid and not expired, create a new user in the `users` table.
  - Delete the record from the `pending_subscriptions` table.
  - Return a success response.

##### Acceptance Criteria
- [ ] Endpoint activates the user's subscription upon successful verification.
- [ ] Endpoint returns an error if the token is invalid or expired.
- [ ] The user is added to the `users` table with `is_active` set to `true`.
- [ ] The corresponding record is removed from `pending_subscriptions`.

---

### Phase 2: Frontend Component Development

#### Task 4: Create Subscription Form Component
**Type:** Frontend
**Dependencies:** None

##### Description
Develop a React component for the subscription form. This component will include an input field for the email address and a submit button.

##### Technical Details
- **File to create:** `frontend/src/components/SubscriptionForm.js`
- **State management:** Handle form input and submission state (loading, success, error).
- **API integration:** Make a `POST` request to the `/subscribe` endpoint.

##### Acceptance Criteria
- [ ] The form validates the email address format on the client-side.
- [ ] The form displays appropriate messages for success and error states.
- [ ] The form is responsive and accessible.

---

#### Task 5: Integrate Subscription Form into Home Page
**Type:** Frontend
**Dependencies:** Task 4

##### Description
Add the `SubscriptionForm` component to the home page, making it easily accessible to new users.

##### Technical Details
- **File to modify:** `frontend/src/components/Home.js`
- **Placement:** Add a "Subscribe" button or embed the form directly on the page.

##### Acceptance Criteria
- [ ] The subscription form is clearly visible on the home page.
- [ ] The user can successfully subscribe from the home page.

---

#### Task 6: Create Email Verification Page
**Type:** Frontend
**Dependencies:** Task 3

##### Description
Create a new page to handle email verification. This page will be the destination for the verification link sent to the user's email. It will display the verification status (success or failure).

##### Technical Details
- **File to create:** `frontend/src/pages/EmailVerificationPage.js`
- **Routing:** Add a new route for `/verify-email`.
- **Logic:**
  - Extract the verification token from the URL.
  - Send a request to the `/verify-email` backend endpoint.
  - Display a success or error message based on the response.

##### Acceptance Criteria
- [ ] The page correctly handles the verification token.
- [ ] The page displays a clear confirmation message upon successful verification.
- [ ] The page displays an error message if verification fails.

---

### Phase 3: Integration & Testing

#### Task 7: End-to-End Subscription Flow Testing
**Type:** Testing
**Dependencies:** Task 3, Task 6

##### Description
Conduct end-to-end testing of the entire subscription journey, from submitting the email to successful verification.

##### Technical Details
- **Manual testing:**
  - Test with valid, invalid, and already subscribed emails.
  - Verify that confirmation emails are sent and links work correctly.
  - Check that the database is updated as expected.
- **Automated testing:**
  - Write unit tests for the new backend endpoints.
  - Write unit tests for the new frontend components.

##### Acceptance Criteria
- [ ] All test scenarios pass successfully.
- [ ] The subscription flow is smooth and bug-free.

---

### Phase 4: Documentation & Cleanup

#### Task 8: Update API Documentation
**Type:** Documentation
**Dependencies:** Task 3

##### Description
Update the API documentation to include the new subscription and verification endpoints.

##### Technical Details
- **File to modify:** `docs/api-reference.md`
- **Content:** Add details for `POST /subscribe` and `GET /verify-email`, including request/response formats.

##### Acceptance Criteria
- [ ] The API documentation is accurate and up-to-date.

## Timeline

- **Phase 1 (Backend):** 2-3 days
- **Phase 2 (Frontend):** 2-3 days
- **Phase 3 (Testing):** 1 day
- **Phase 4 (Documentation):** 1 day
- **Total Estimated Time:** 6-8 days

## Risk Assessment

- **Email Delivery:** Ensure the email service is reliable. Have a fallback or monitoring in place.
- **Security:** Verification tokens must be secure and have a limited lifespan to prevent misuse.
- **User Experience:** The subscription flow should be as simple as possible to maximize conversions.

## Success Criteria

- A new user can successfully subscribe and verify their email through the web interface.
- The system correctly handles all scenarios, including errors and existing subscriptions.
- The implementation is robust, secure, and well-documented.
