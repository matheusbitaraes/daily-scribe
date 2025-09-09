# User Story: User Unsubscription

**As a** subscribed user,
**I want to** be able to easily unsubscribe from the daily digest,
**So that** I can stop receiving emails I no longer want.

## Acceptance Criteria

-   Every digest email contains a clear and easy-to-find "Unsubscribe" link in the footer.
-   Clicking the "Unsubscribe" link takes the user to a confirmation page.
-   The unsubscription page gives the user a one-click option to confirm they want to unsubscribe.
-   Upon confirming, the user is immediately removed from the active subscriber list.
-   The user sees a confirmation message on the website that they have been successfully unsubscribed.
-   The user does not receive any further digest emails.

## Scenarios

### Scenario 1: Successful Unsubscription from Email

-   **Given** a user has received a daily digest email.
-   **When** they click the "Unsubscribe" link in the email footer.
-   **Then** they are taken to an unsubscription confirmation page.
-   **When** they click the "Confirm Unsubscribe" button.
-   **Then** they see a message confirming their unsubscription.
-   **And** their email address is marked as inactive in the database.
-   **And** they no longer receive daily digests.

### Scenario 2: Unsubscribing from Preferences Page

-   **Given** a user is on their preferences management page.
-   **When** they click the "Unsubscribe" button.
-   **Then** they are shown a confirmation dialog.
-   **When** they confirm they want to unsubscribe.
-   **Then** they are unsubscribed and redirected to a confirmation page.
-   **And** their email address is marked as inactive in the database.
-   **And** they no longer receive daily digests.

### Scenario 3: Accidental Unsubscribe Click

-   **Given** a user has clicked the "Unsubscribe" link from an email.
-   **And** they are on the unsubscription confirmation page.
-   **When** they close the page or navigate away without confirming.
-   **Then** their subscription remains active.
-   **And** they continue to receive daily digests.
