# Roadmap

- [x] RSS feed fetching and parsing
- [x] External model (Gemini API integration)
- [x] Handle rate limiting from the LLM API
- [x] Improve digest format and language
- [x] store publication date in the artice table as well as creation date in our side
- [x] Develop a categorization approach - implement a metadata extractor?
- [x] divide extraction of content and diggest to be different processes
- [x] Daily digest generation and scheduling
- [x] Email delivery system
- [x] create below users
      Smendes.ana@gmail.com
      fsnader@gmail.com
      nikolas.memo@gmail.com
      pareidoliza@gmail.com
      onolupo@msn.com
      daniel.hesanto@gmail.com
      lucasaugustorl@hotmail.com
- [x] Add a new table to track in which digest the articles were sent
- [x] Have a new column in sources that will hide them from ones email diggest (but we will keep on fetching the article news)
- [x] Advanced content filtering and categorization -> add a way to curate content when digest is really big - check [here](https://gemini.google.com/gem/fdc459572bee/7c4574e44151bd6c)
- [x] Similar news showing clustered
- [x] send source in digest
- [x] fix ordering
- [x] split article fetch from article summarization 
      - store originals 
      - create a layer for translating each different rss?
- [x] clean html encodings on rss parsing
- [x] Web interface for configuration management
   - be able to check and experiment some news grouping and experiment clusters
   - be able to test email digests
   - have a good and simple UI
- [x] add summary_pt
- [x] Check sources on clustering
- [x] Improve documentation for AI
- [x] Complete frontend deployment integration
- [x] Update technical documentation with current API endpoints
- [x] Create comprehensive API reference guide
- [x] Add frontend development guide
- [x] Create end-user documentation
- [x] Home page
- [x] Web interface to subscription - home page
      - Make a home page with a subscribe button? Or make a subscribe landing page?
      - make an unsubscribe button in the email as well
- [x] change email provider - now its @dailyscribe.news
- [x] Publicly expose frontend so that user preferences can be changed
- [x] Cleanup components/notifier.py
- [x] kill config.json
- [x] Revamp all the design
      - [x] home page
      - [x] subscribe
      - [x] unsubscribe
      - [x] preferences
- [x] cronojob to backup db and cleanup
- [x] Improve curator quality; extract if its hard or soft news, try extracting the importance or weight of the news, ... research on more to extract
      - [x] Ao invés de ‘Suas Notícias de 15/09/2025’, uns top 3 assuntos. store a headline_pt
      - Translation API to title? or title_pt?
- [x] ui bug on source selection 
- [x] add save button
- [x] home page with news in tabs
- [x] reference to home page in email
- [x] redirect urls in email
- [x] titles in portuguese
- [x] Add some sort of cache to the news page?
- [x] Improve grafana logs and dashboards
- [x] improve email experience - today, there are too many news
      - [x] add a page that will display only one article with all information available, with a button that goes to the news feed
      - [x] Get x headline articles. Create rules to define how to define those.
- [x] news page for mobile
- [x] add preferences during user onboarding
- [x] add elasticsearch db 
      - do a simple search term [x]
      - how to index? which frequency? [x]
      - script to read from all backups - no need for now
- [ ] Improve ranking
      - [ ] home page
      - [ ] email digest
- [ ] cleanup code: 
      Improve copilot agent rules and documentation
      remove unused cripts
- [ ] make digest builder admin only


