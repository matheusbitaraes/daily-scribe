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
- [ ] kill config.json
- [ ] make digest builder admin only
- [ ] Revamp all the design
      - [ ] home page
      - [ ] subscribe
      - [ ] unsubscribe
      - [ ] preferences
- [ ] titles on portuguese
- [ ] Improva grafana logs and dashboards
- [ ] migrate db to elasticsearch?