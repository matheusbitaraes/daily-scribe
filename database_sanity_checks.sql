-- ===========================================================================
-- Daily Scribe Database Sanity Checks
-- ===========================================================================
-- This file contains SQL queries to validate database health and identify 
-- potential issues with the data processing pipeline.
--
-- Tables involved:
-- - articles: Main article storage with metadata
-- - sources: News sources configuration  
-- - rss_feeds: RSS feed URLs for each source
-- - sent_articles: Tracking of articles sent to users
-- - user_preferences: User subscription settings
-- - article_embeddings: Vector embeddings for ML features
-- - article_clusters: Article clustering results
-- ===========================================================================

-- CHECK 1: Articles without summary/summary_pt but raw_content is null (processed yesterday)
-- This indicates articles that were marked as processed but failed content extraction
-- ======================================================================================
SELECT 
    'Articles processed yesterday missing both content and summary' as check_name,
    COUNT(*) as issue_count,
    'CRITICAL' as severity
FROM articles a
LEFT JOIN sources s ON a.source_id = s.id
WHERE DATE(a.processed_at) = DATE('now', '-1 day')
  AND (a.summary IS NULL AND a.summary_pt IS NULL)
  AND a.raw_content IS NULL;

-- Details for the above check
SELECT 
    a.id,
    a.url,
    a.title,
    s.name as source_name,
    a.processed_at,
    a.published_at,
    'Missing content and summary' as issue
FROM articles a
LEFT JOIN sources s ON a.source_id = s.id
WHERE DATE(a.processed_at) = DATE('now', '-1 day')
  AND (a.summary IS NULL AND a.summary_pt IS NULL)
  AND a.raw_content IS NULL
ORDER BY a.processed_at DESC;

-- CHECK 2: No articles processed in last 5 hours
-- This indicates the RSS processor or content pipeline may be down
-- ================================================================
SELECT 
    'Articles processed in last 5 hours' as check_name,
    COUNT(*) as article_count,
    CASE 
        WHEN COUNT(*) = 0 THEN 'CRITICAL'
        WHEN COUNT(*) < 10 THEN 'WARNING'
        ELSE 'OK'
    END as severity,
    MAX(processed_at) as last_processed_at
FROM articles 
WHERE processed_at >= datetime('now', '-5 hours');

-- CHECK 3: No articles with summary/summary_pt in last 5 hours  
-- This indicates the NLP/summarization pipeline may be down
-- =========================================================
SELECT 
    'Articles with summaries in last 5 hours' as check_name,
    COUNT(*) as article_count,
    CASE 
        WHEN COUNT(*) = 0 THEN 'CRITICAL'
        WHEN COUNT(*) < 5 THEN 'WARNING'
        ELSE 'OK'
    END as severity,
    MAX(processed_at) as last_summarized_at
FROM articles 
WHERE processed_at >= datetime('now', '-5 hours')
  AND (summary IS NOT NULL OR summary_pt IS NOT NULL);

-- CHECK 4: Articles with raw_content but no summary after 24 hours
-- This indicates the summarization pipeline is lagging behind content extraction
-- ============================================================================
SELECT 
    'Articles with content but no summary after 24h' as check_name,
    COUNT(*) as issue_count,
    'WARNING' as severity
FROM articles 
WHERE raw_content IS NOT NULL 
  AND (summary IS NULL AND summary_pt IS NULL)
  AND processed_at < datetime('now', '-24 hours');

-- Details for the above check
SELECT 
    a.id,
    a.url,
    a.title,
    s.name as source_name,
    a.processed_at,
    LENGTH(a.raw_content) as content_length,
    'Has content but missing summary' as issue
FROM articles a
LEFT JOIN sources s ON a.source_id = s.id
WHERE a.raw_content IS NOT NULL 
  AND (a.summary IS NULL AND a.summary_pt IS NULL)
  AND a.processed_at < datetime('now', '-24 hours')
ORDER BY a.processed_at DESC
LIMIT 20;

-- CHECK 5: Duplicate articles by URL
-- This indicates potential issues with URL deduplication
-- ====================================================
SELECT 
    'Duplicate articles by URL' as check_name,
    COUNT(*) as duplicate_count,
    CASE 
        WHEN COUNT(*) > 0 THEN 'WARNING'
        ELSE 'OK'
    END as severity
FROM (
    SELECT url, COUNT(*) as count
    FROM articles 
    GROUP BY url 
    HAVING COUNT(*) > 1
);

-- Details for duplicate URLs
SELECT 
    url,
    COUNT(*) as duplicate_count,
    GROUP_CONCAT(id) as article_ids,
    MIN(processed_at) as first_processed,
    MAX(processed_at) as last_processed
FROM articles 
GROUP BY url 
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC, first_processed DESC;

-- CHECK 6: Articles missing critical metadata
-- This identifies articles that may have failed metadata extraction
-- ================================================================
SELECT 
    'Articles missing title or category in last 24h' as check_name,
    COUNT(*) as issue_count,
    CASE 
        WHEN COUNT(*) > 50 THEN 'CRITICAL'
        WHEN COUNT(*) > 10 THEN 'WARNING'
        ELSE 'OK'
    END as severity
FROM articles 
WHERE processed_at >= datetime('now', '-24 hours')
  AND (title IS NULL OR title = '' OR category IS NULL OR category = '');

-- CHECK 7: RSS Feeds health
-- Check if all enabled feeds have recent articles
-- ==============================================
SELECT 
    'Enabled RSS feeds without recent articles (48h)' as check_name,
    COUNT(*) as stale_feed_count,
    CASE 
        WHEN COUNT(*) > 2 THEN 'WARNING'
        WHEN COUNT(*) > 0 THEN 'INFO'
        ELSE 'OK'
    END as severity
FROM rss_feeds rf
LEFT JOIN sources s ON rf.source_id = s.id
LEFT JOIN articles a ON a.source_id = s.id AND a.processed_at >= datetime('now', '-48 hours')
WHERE rf.is_enabled = 1
  AND a.id IS NULL;

-- Details for stale RSS feeds
SELECT 
    s.name as source_name,
    rf.url as feed_url,
    rf.is_enabled,
    COUNT(a.id) as recent_articles,
    MAX(a.processed_at) as last_article_processed
FROM rss_feeds rf
LEFT JOIN sources s ON rf.source_id = s.id
LEFT JOIN articles a ON a.source_id = s.id AND a.processed_at >= datetime('now', '-48 hours')
WHERE rf.is_enabled = 1
GROUP BY rf.id, s.name, rf.url
ORDER BY recent_articles ASC, last_article_processed ASC;

-- CHECK 8: Database growth rate
-- Monitor database growth to detect unusual spikes
-- ===============================================
SELECT 
    'Database growth analysis' as check_name,
    DATE(processed_at) as date,
    COUNT(*) as articles_per_day,
    AVG(LENGTH(COALESCE(raw_content, ''))) as avg_content_length,
    SUM(CASE WHEN summary IS NOT NULL OR summary_pt IS NOT NULL THEN 1 ELSE 0 END) as articles_with_summaries
FROM articles 
WHERE processed_at >= datetime('now', '-7 days')
GROUP BY DATE(processed_at)
ORDER BY date DESC;

-- CHECK 9: Articles with exceptionally long or short content
-- Identify potential content extraction issues
-- ===========================================
SELECT 
    'Articles with unusual content length in last 24h' as check_name,
    COUNT(*) as issue_count,
    'INFO' as severity
FROM articles 
WHERE processed_at >= datetime('now', '-24 hours')
  AND raw_content IS NOT NULL
  AND (LENGTH(raw_content) < 100 OR LENGTH(raw_content) > 100000);

-- CHECK 10: Missing article embeddings
-- Check if ML pipeline is keeping up with new articles
-- ===================================================
SELECT 
    'Articles without embeddings older than 6 hours' as check_name,
    COUNT(*) as missing_embeddings_count,
    CASE 
        WHEN COUNT(*) > 100 THEN 'WARNING'
        WHEN COUNT(*) > 0 THEN 'INFO'
        ELSE 'OK'
    END as severity
FROM articles a
LEFT JOIN article_embeddings ae ON a.id = ae.article_id
WHERE a.processed_at < datetime('now', '-6 hours')
  AND (a.summary IS NOT NULL OR a.summary_pt IS NOT NULL)
  AND ae.article_id IS NULL;

-- CHECK 11: Source distribution health
-- Ensure we're getting articles from all expected sources
-- ======================================================
SELECT 
    'Source distribution in last 24 hours' as check_name,
    s.name as source_name,
    COUNT(a.id) as article_count,
    MAX(a.processed_at) as last_article,
    CASE 
        WHEN COUNT(a.id) = 0 THEN 'WARNING'
        WHEN COUNT(a.id) < 5 THEN 'INFO'
        ELSE 'OK'
    END as status
FROM sources s
LEFT JOIN articles a ON s.id = a.source_id AND a.processed_at >= datetime('now', '-24 hours')
GROUP BY s.id, s.name
ORDER BY article_count DESC;

-- CHECK 12: Email digest activity
-- Monitor if digests are being sent regularly
-- ==========================================
SELECT 
    'Digest activity in last 24 hours' as check_name,
    COUNT(DISTINCT email_address) as unique_recipients,
    COUNT(*) as total_articles_sent,
    COUNT(DISTINCT digest_id) as unique_digests,
    MAX(sent_at) as last_digest_sent,
    CASE 
        WHEN COUNT(DISTINCT digest_id) = 0 THEN 'WARNING'
        ELSE 'OK'
    END as status
FROM sent_articles 
WHERE sent_at >= datetime('now', '-24 hours');

-- CHECK 13: User subscription health
-- Monitor user engagement and subscription status
-- =============================================
SELECT 
    'Active user subscriptions' as check_name,
    COUNT(*) as total_users,
    COUNT(CASE WHEN enabled_categories IS NOT NULL THEN 1 END) as users_with_preferences,
    'INFO' as severity
FROM user_preferences;

-- CHECK 14: Token usage and security
-- Monitor token-based authentication
-- ================================
SELECT 
    'Token security status' as check_name,
    COUNT(*) as total_tokens,
    COUNT(CASE WHEN is_revoked = 1 THEN 1 END) as revoked_tokens,
    COUNT(CASE WHEN expires_at < datetime('now') THEN 1 END) as expired_tokens,
    COUNT(CASE WHEN usage_count >= max_usage THEN 1 END) as exhausted_tokens,
    'INFO' as severity
FROM user_tokens;

-- CHECK 15: Database integrity constraints
-- Verify foreign key relationships are intact
-- ==========================================
SELECT 
    'Articles with invalid source_id references' as check_name,
    COUNT(*) as issue_count,
    CASE 
        WHEN COUNT(*) > 0 THEN 'CRITICAL'
        ELSE 'OK'
    END as severity
FROM articles a
LEFT JOIN sources s ON a.source_id = s.id
WHERE s.id IS NULL;

-- CHECK 16: Recent processing performance
-- Monitor processing latency between published_at and processed_at
-- ===============================================================
SELECT 
    'Processing delay analysis (last 24h)' as check_name,
    COUNT(*) as total_articles,
    AVG(
        CASE 
            WHEN published_at IS NOT NULL THEN 
                (julianday(processed_at) - julianday(published_at)) * 24 * 60
            ELSE NULL
        END
    ) as avg_delay_minutes,
    MAX(
        CASE 
            WHEN published_at IS NOT NULL THEN 
                (julianday(processed_at) - julianday(published_at)) * 24 * 60
            ELSE NULL
        END
    ) as max_delay_minutes,
    'INFO' as severity
FROM articles 
WHERE processed_at >= datetime('now', '-24 hours')
  AND published_at IS NOT NULL
  AND published_at <= processed_at;

-- CHECK 17: System health summary
-- Overall system health dashboard
-- ==============================
SELECT 
    'System Health Summary' as dashboard,
    (SELECT COUNT(*) FROM articles WHERE processed_at >= datetime('now', '-1 hour')) as articles_last_hour,
    (SELECT COUNT(*) FROM articles WHERE processed_at >= datetime('now', '-24 hours')) as articles_last_24h,
    (SELECT COUNT(*) FROM articles WHERE (summary IS NOT NULL OR summary_pt IS NOT NULL) AND processed_at >= datetime('now', '-1 hour')) as summarized_last_hour,
    (SELECT COUNT(*) FROM sources) as total_sources,
    (SELECT COUNT(*) FROM rss_feeds WHERE is_enabled = 1) as enabled_feeds,
    (SELECT COUNT(*) FROM user_preferences) as active_users,
    (SELECT MAX(processed_at) FROM articles) as last_article_processed;