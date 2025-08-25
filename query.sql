--SELECT * FROM articles

--ALTER TABLE articles ADD COLUMN title TEXT;

-- delete from articles
-- where id > 0

--select * from sources;

-- -- WSJ
-- INSERT INTO rss_feeds (source_id, url) VALUES (1, 'https://feeds.a.dj.com/rss/RSSWorldNews.xml');
-- INSERT INTO rss_feeds (source_id, url) VALUES (1, 'https://feeds.a.dj.com/rss/RSSWorldNews.xml');

-- -- G1 Globo
-- INSERT INTO rss_feeds (source_id, url) VALUES (2, 'http://g1.globo.com/dynamo/brasil/rss2.xml');
-- INSERT INTO rss_feeds (source_id, url) VALUES (2, 'http://g1.globo.com/dynamo/brasil/rss2.xml');
-- INSERT INTO rss_feeds (source_id, url) VALUES (2, 'http://g1.globo.com/dynamo/economia/rss2.xml');
-- INSERT INTO rss_feeds (source_id, url) VALUES (2, 'http://g1.globo.com/dynamo/tecnologia/rss2.xml');
-- INSERT INTO rss_feeds (source_id, url) VALUES (2, 'http://g1.globo.com/dynamo/economia/rss2.xml');
-- INSERT INTO rss_feeds (source_id, url) VALUES (2, 'http://g1.globo.com/dynamo/tecnologia/rss2.xml');

-- -- The Guardian
-- INSERT INTO rss_feeds (source_id, url) VALUES (3, 'https://www.theguardian.com/world/rss');

-- -- TechCrunch
-- INSERT INTO rss_feeds (source_id, url) VALUES (4, 'https://techcrunch.com/feed/');
-- INSERT INTO rss_feeds (source_id, url) VALUES (4, 'https://techcrunch.com/category/startups/feed/');

-- -- Wired
-- INSERT INTO rss_feeds (source_id, url) VALUES (5, 'https://www.wired.com/feed/rss');

-- -- The Verge
-- INSERT INTO rss_feeds (source_id, url) VALUES (6, 'https://www.theverge.com/rss/index.xml');

-- -- Bloomberg
-- INSERT INTO rss_feeds (source_id, url) VALUES (7, 'https://feeds.bloomberg.com/markets/news.rss');

-- -- Investing.com
-- INSERT INTO rss_feeds (source_id, url) VALUES (8, 'https://www.investing.com/rss/news.rss');

-- -- Reuters
-- INSERT INTO rss_feeds (source_id, url) VALUES (9, 'http://feeds.reuters.com/reuters/businessNews');
-- INSERT INTO rss_feeds (source_id, url) VALUES (9, 'http://feeds.reuters.com/Reuters/worldNews');

-- -- NASA
-- INSERT INTO rss_feeds (source_id, url) VALUES (10, 'https://www.nasa.gov/rss/image_of_the_day.rss');
-- INSERT INTO rss_feeds (source_id, url) VALUES (10, 'https://www.nasa.gov/rss/breaking_news.rss');

-- -- National Geographic
-- INSERT INTO rss_feeds (source_id, url) VALUES (11, 'https://www.nationalgeographic.com/science/rss-feed.xml');

-- -- ScienceDaily
-- INSERT INTO rss_feeds (source_id, url) VALUES (12, 'http://feeds.sciencedaily.com/sciencedaily');

-- -- Folha
-- INSERT INTO rss_feeds (source_id, url) VALUES (13, 'https://feeds.folha.uol.com.br/poder/rss.xml');
-- INSERT INTO rss_feeds (source_id, url) VALUES (13, 'https://feeds.folha.uol.com.br/mercado/rss.xml');
-- INSERT INTO rss_feeds (source_id, url) VALUES (13, 'https://feeds.folha.uol.com.br/tec/rss.xml');

-- -- Estadao
-- INSERT INTO rss_feeds (source_id, url) VALUES (14, 'https://www.estadao.com.br/arc/outboundfeeds/feeds/rss/sections/politica/');
-- INSERT INTO rss_feeds (source_id, url) VALUES (14, 'https://www.estadao.com.br/arc/outboundfeeds/feeds/rss/sections/economia/');
-- INSERT INTO rss_feeds (source_id, url) VALUES (14, 'https://www.estadao.com.br/arc/outboundfeeds/feeds/rss/sections/esportes/');

-- -- UOL
-- INSERT INTO rss_feeds (source_id, url) VALUES (15, 'http://rss.uol.com.br/feed/noticias.xml');
-- INSERT INTO rss_feeds (source_id, url) VALUES (15, 'http://rss.uol.com.br/feed/tecnologia.xml');
-- INSERT INTO rss_feeds (source_id, url) VALUES (15, 'http://rss.uol.com.br/feed/economia.xml');

-- -- Agencia Brasil
-- INSERT INTO rss_feeds (source_id, url) VALUES (16, 'https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml');

-- -- Banco Central do Brasil
-- INSERT INTO rss_feeds (source_id, url) VALUES (17, 'https://www.bcb.gov.br/api/servico/sitebcb/rss?nome=Noticias');
-- INSERT INTO rss_feeds (source_id, url) VALUES (17, 'https://www.bcb.gov.br/api/servico/sitebcb/rss?nome=CopomAta');

-- -- CNN
-- INSERT INTO rss_feeds (source_id, url) VALUES (18, 'http://rss.cnn.com/rss/edition.rss');

-- -- NY Times
-- INSERT INTO rss_feeds (source_id, url) VALUES (19, 'http://feeds.nytimes.com/nyt/rss/HomePage');

-- -- BBC
-- INSERT INTO rss_feeds (source_id, url) VALUES (20, 'http://feeds.bbci.co.uk/news/world/rss.xml');

-- -- Le Monde
-- INSERT INTO rss_feeds (source_id, url) VALUES (21, 'https://www.lemonde.fr/en/international/rss_full.xml');

-- -- Washington Post
-- INSERT INTO rss_feeds (source_id, url) VALUES (22, 'https://feeds.washingtonpost.com/rss/world');

delete from rss_feeds
where id = 3;