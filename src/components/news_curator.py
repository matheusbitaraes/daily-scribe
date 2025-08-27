from collections import defaultdict
from components.database import DatabaseService

class NewsCurator:
    """
    Curates articles for the digest based on configurable rules and user preferences.
    """
    def __init__(self,):
        self.db_service = DatabaseService()

    def curate_for_user(self, email_address):
        """
        Select up to max_per_category articles per category, filtered by user preferences.
        Assumes each article has a 'category' field (str or list of str) and a 'source_id' or 'source' field.
        """
        # Get user preferences
        prefs = self.db_service.get_user_preferences(email_address)
        
        # print prefs:
        print(prefs)

        enabled_sources = prefs['enabled_sources'] if prefs and prefs.get('enabled_sources') else None
        enabled_categories = prefs['enabled_categories'] if prefs and prefs.get('enabled_categories') else None
        max_news_per_category = prefs['max_news_per_category'] if prefs and prefs.get('max_news_per_category') is not None else 10

        articles = self.db_service.get_unsent_articles(
            email_address,
            enabled_sources=[str(s) for s in enabled_sources] if enabled_sources else None,
            enabled_categories=enabled_categories
        )
        curated = []
        category_counts = defaultdict(int)
        for article in articles:
            categories = article.get('category')
            if not categories:
                categories = ['uncategorized']
            elif isinstance(categories, str):
                categories = [categories]
            added = False
            for cat in categories:
                if category_counts[cat] < max_news_per_category:    
                    curated.append(article)
                    for c in categories:
                        category_counts[c] += 1
                    added = True
                    break
            if added:
                continue
        return curated
