# User Story: Email Feedback for Personalized Ranking

**As a** Daily Scribe subscriber,
**I want to** quickly signal which stories match my interests directly from the digest email,
**So that** the system can learn my preferences and tailor future briefings without forcing me to leave my inbox.

## Acceptance Criteria

- The daily digest email shows two lightweight feedback actions ("Mais como esta" and "Menos como esta") beside each highlighted story.
- Clicking a feedback action records the reader's signal via the secure API token associated with that digest.
- The interaction feels instantaneous: a minimal confirmation page appears (or the tab closes) without interrupting the reading flow.
- Positive feedback increases the likelihood of similar content appearing in future digests; negative feedback reduces it.
- Recorded signals update both the user's semantic profile and their personalized ranking weights within seconds.
- The system stores feedback logs (story, signal, digest id, timestamp) for observability and future analysis.

## Scenarios

### Scenario 1: Positive Feedback from Email
- **Given** a subscriber opens the Daily Scribe email and sees a top story that resonates with their interests,
- **When** they click the "Mais como esta" button,
- **Then** a short confirmation page appears thanking them for the feedback,
- **And** the system records a positive signal tied to that article and digest,
- **And** their user embedding is updated immediately to boost similar content.

### Scenario 2: Negative Feedback from Email
- **Given** a subscriber sees an article that is irrelevant to them,
- **When** they click the "Menos como esta" button,
- **Then** a short confirmation page appears acknowledging the preference,
- **And** the system records a negative signal for that story,
- **And** their personalized ranking weights shift to surface fewer stories like it.

### Scenario 3: Feedback Attempt with Expired Token
- **Given** a subscriber opens an old digest whose secure token has already expired,
- **When** they click either feedback action,
- **Then** a friendly message explains that the feedback window has closed,
- **And** no signal is recorded.
