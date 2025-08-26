from collections import defaultdict
from components.database import DatabaseService

class NewsCurator:
    """
    Curates articles for the digest based on configurable rules.
    """
    def __init__(self, max_per_category: int = 10):
        self.max_per_category = max_per_category
        self.db_service = DatabaseService()

    def curate_for_user(self, email_address):
        """
        Select up to max_per_category articles per category.
        Assumes each article has a 'category' field (str or list of str).
        """

        articles = self.db_service.get_unsent_articles(email_address)
        curated = []
        category_counts = defaultdict(int)
        for article in articles:
            # Support both string and list for category
            categories = article.get('category')
            if not categories:
                categories = ['uncategorized']
            elif isinstance(categories, str):
                categories = [categories]
            added = False
            for cat in categories:
                if category_counts[cat] < self.max_per_category:
                    curated.append(article)
                    for c in categories:
                        category_counts[c] += 1
                    added = True
                    break
            if added:
                continue
        return curated
