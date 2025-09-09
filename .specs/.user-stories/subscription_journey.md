# User Story: User Subscription

**As a** new user,
**I want to** be able to subscribe to the daily digest through a simple web interface,
**So that** I can start receiving daily news summaries.

## Acceptance Criteria

-   A clear "Subscribe" call-to-action is visible on the home page.
-   Clicking the "Subscribe" button takes the user to a subscription page/modal.
-   The subscription form requires the user to enter a valid email address.
-   After submitting the email, the user receives a confirmation email to verify their address.
-   The user's email is not added to the active subscriber list until it is verified.
-   Upon successful subscription and verification, the user sees a confirmation message on the website.
-   The new subscriber is added to the database with default preferences.

## Scenarios

### Scenario 1: Successful Subscription

-   **Given** a user is on the Daily Scribe home page.
-   **When** they click the "Subscribe" button.
-   **And** they enter a valid email address (e.g., "new.subscriber@example.com").
-   **And** they click "Subscribe".
-   **Then** they see a message instructing them to check their email for a verification link.
-   **And** they receive an email with a verification link.
-   **When** they click the verification link.
-   **Then** they are taken to a confirmation page.
-   **And** their email is added to the subscriber list.
-   **And** they start receiving the daily digest from the next day.

### Scenario 2: Invalid Email Address

-   **Given** a user is on the subscription page.
-   **When** they enter an invalid email address (e.g., "not-an-email").
-   **And** they click "Subscribe".
-   **Then** they see an error message indicating the email format is invalid.
-   **And** their email is not submitted.

### Scenario 3: Already Subscribed Email

-   **Given** a user is on the subscription page.
-   **When** they enter an email address that is already subscribed.
-   **And** they click "Subscribe".
-   **Then** they see a message indicating that this email is already subscribed.
-   **And** they are given a link to manage their preferences.
