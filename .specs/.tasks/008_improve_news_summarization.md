Improve news summarization:

# Tasks
## 1 - Create three new database fields, including db migrations: ✓ Completed
    urgency_score (int, 1 to 5)
    impact_score (int, 1 to 5)
    subject_pt (string: 2 - 3 words representing the headline for putting into an email)
## 2 - During summarization phase, also ask for the models to fill those three fields, according to below prompts: ✓ Completed
Of course! Here is a prompt you can use to explain the news classification task to an agent.


*Urgency score* 
This scale measures how quickly the information in the news article loses its relevance.

1 - Evergreen: The content is timeless and remains relevant indefinitely.

Examples: An article explaining a scientific concept, a historical analysis, or a biography of a historical figure.

2 - Long-Term: The information is relevant for an extended period, like several weeks or months, but is not tied to a current event.

Examples: A report on industry trends for the upcoming quarter or an in-depth analysis of a social movement.

3 - Topical: The story relates to recent events but is not breaking. It provides follow-up or analysis.

Examples: A day-after analysis of a political speech or a summary of the week's market performance.

4 - Time-Sensitive: The information is urgent and requires attention within a day or two, after which its value significantly decreases.

Examples: A weather warning for the next 48 hours, an announcement for an event happening this week, or a time-limited promotional offer.

5 - Breaking News: The event is happening right now or has just occurred. The information is new and developing.

Examples: Reports of an ongoing natural disaster, live election results being announced, or a sudden major political event.

*Impact Score*
This scale measures the significance of the news—how many people are affected and to what degree.

1 - Minor Update: The information has a very low impact, affecting a small number of people or representing a trivial change.

Examples: A minor bug fix in a software update, a small personnel change in a large corporation, or a routine local traffic update.

2 - Niche Impact: The news is significant but only to a specific community, industry, or hobbyist group.

Examples: New regulations affecting a single industry, results from a local community sports league, or updates to a niche video game.

3 - Moderate Impact: The news affects a large community or a significant demographic, causing a noticeable but not fundamental change.

Examples: The opening of a new public library in a large town, a policy change for a single school district, or a popular company launching a new but expected product.

4. - Significant Impact: The news has major consequences for an entire region, country, or industry. It will likely lead to substantial changes.

Examples: A new national law on taxation, a major international trade agreement, or a large corporation filing for bankruptcy.

5 - Major Development: This is a landmark event with profound, widespread, and potentially historic consequences on a national or global scale.

Examples: The outbreak of a global pandemic, the beginning of an international war, a global financial market crash, or a revolutionary scientific discovery.

*subject_pt* 
This score represents a very short 2-3 words phrase that can be used to compose the subject of an email.

Then propely store the results in the database.

## 3 - Update the news curator to order the articles by urgency_score and impact_score. From getting the relevance list, order by urgency_score and impact_score. ✓ Completed

## 4 - Update the email composer to include subject_pt in the email subject composition. It should get the first 3 news with the highest urgency_score and impact_score. ✓ Completed

## Relevant Files

### Backend Files
- `src/utils/migrations.py` - Added migration 007_add_news_scoring_fields for urgency_score, impact_score, subject_pt columns
- `src/components/database.py` - Updated database queries and methods to handle new scoring fields
- `src/components/summarizer.py` - Enhanced NewsMetadata model with new fields and detailed scoring prompts
- `src/components/news_curator.py` - Updated article sorting to prioritize urgency_score and impact_score
- `src/components/digest_service.py` - Added email subject generation using top 3 highest scoring articles