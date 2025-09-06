import React, { useRef, useEffect } from 'react';
import DOMPurify from 'dompurify';
import './DigestPreview.css';

const DigestPreview = ({ 
  digestContent, 
  digestMetadata, 
  isLoading = false, 
  error = null 
}) => {
  const iframeRef = useRef(null);

  // Sanitize HTML content for security
  const sanitizedContent = digestContent 
    ? DOMPurify.sanitize(digestContent, {
        ALLOWED_TAGS: ['div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'strong', 'em', 'u', 'br', 'hr', 'ul', 'ol', 'li', 'img', 'table', 'tr', 'td', 'th', 'thead', 'tbody', 'span', 'blockquote'],
        ALLOWED_ATTR: ['href', 'target', 'rel', 'src', 'alt', 'title', 'class', 'id', 'style'],
        ALLOW_DATA_ATTR: false
      })
    : '';

  // Update iframe content when digestContent changes
  useEffect(() => {
    if (iframeRef.current && sanitizedContent) {
      const iframe = iframeRef.current;
      const doc = iframe.contentDocument || iframe.contentWindow.document;
      
      // Create a complete HTML document for the iframe
      const fullHtml = `
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>Digest Preview</title>
          <style>
            body {
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
              line-height: 1.6;
              color: #333;
              max-width: 600px;
              margin: 0 auto;
              padding: 20px;
              background-color: #ffffff;
            }
            h1, h2, h3 {
              color: #2d3748;
              margin-top: 24px;
              margin-bottom: 16px;
            }
            h1 { font-size: 24px; }
            h2 { font-size: 20px; }
            h3 { font-size: 18px; }
            p {
              margin-bottom: 16px;
            }
            a {
              color: #3182ce;
              text-decoration: none;
            }
            a:hover {
              text-decoration: underline;
            }
            .article-cluster {
              margin-bottom: 32px;
              padding: 16px;
              border-left: 4px solid #3182ce;
              background-color: #f7fafc;
            }
            .article-item {
              margin-bottom: 16px;
              padding: 12px;
              background-color: white;
              border-radius: 8px;
              box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }
            .article-title {
              font-weight: 600;
              font-size: 16px;
              margin-bottom: 8px;
            }
            .article-summary {
              color: #4a5568;
              font-size: 14px;
              margin-bottom: 8px;
            }
            .article-meta {
              font-size: 12px;
              color: #718096;
              display: flex;
              gap: 16px;
            }
            .cluster-title {
              font-size: 18px;
              font-weight: 600;
              color: #2d3748;
              margin-bottom: 16px;
            }
            hr {
              border: none;
              border-top: 1px solid #e2e8f0;
              margin: 24px 0;
            }
            img {
              max-width: 100%;
              height: auto;
              border-radius: 4px;
            }
            table {
              width: 100%;
              border-collapse: collapse;
              margin: 16px 0;
            }
            th, td {
              padding: 8px 12px;
              text-align: left;
              border-bottom: 1px solid #e2e8f0;
            }
            th {
              background-color: #f7fafc;
              font-weight: 600;
            }
          </style>
        </head>
        <body>
          ${sanitizedContent}
        </body>
        </html>
      `;
      
      doc.open();
      doc.write(fullHtml);
      doc.close();
      
      // Ensure all links open in new tab/window
      const links = doc.querySelectorAll('a');
      links.forEach(link => {
        link.setAttribute('target', '_blank');
        link.setAttribute('rel', 'noopener noreferrer');
      });
    }
  }, [sanitizedContent]);

  // Loading state
  if (isLoading) {
    return (
      <div className="digest-preview">
        <div className="preview-header">
          <h2>Digest Preview</h2>
        </div>
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Generating digest preview...</p>
          <div className="loading-details">
            <span>Processing articles...</span>
            <span>Creating clusters...</span>
            <span>Formatting content...</span>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="digest-preview">
        <div className="preview-header">
          <h2>Digest Preview</h2>
        </div>
        <div className="error-state">
          <div className="error-icon">⚠️</div>
          <h3>Failed to Generate Digest</h3>
          <p>{error}</p>
          <div className="error-suggestions">
            <p>Try the following:</p>
            <ul>
              <li>Check that you've entered a valid email address</li>
              <li>Ensure there are articles available for the selected date</li>
              <li>Verify your internet connection</li>
              <li>Try refreshing the page</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  // No content state
  if (!digestContent) {
    return (
      <div className="digest-preview">
        <div className="preview-header">
          <h2>Digest Preview</h2>
        </div>
        <div className="empty-state">
          <div className="empty-icon">📧</div>
          <h3>No Digest to Preview</h3>
          <p>Select a date and click "Generate Digest Preview" to see your personalized news digest.</p>
          <div className="preview-features">
            <div className="feature-list">
              <div className="feature-item">
                <span className="feature-icon">📰</span>
                <span>Curated articles based on your preferences</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">🎯</span>
                <span>Intelligent clustering and summarization</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">📱</span>
                <span>Mobile-friendly formatting</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Main content display
  return (
    <div className="digest-preview">
      <div className="preview-header">
        <h2>Digest Preview</h2>
      </div>

      <div className="preview-content">
        <div className="iframe-container">
          <iframe
            ref={iframeRef}
            className="digest-iframe"
            title="Digest Preview"
            sandbox="allow-same-origin"
          />
        </div>
      </div>

      <div className="preview-footer">
        <div className="preview-info">
          <p>
            <strong>📧 This is how your digest will appear in email.</strong>
            All links will open in new tabs when clicked.
          </p>
        </div>
      </div>
    </div>
  );
};

export default DigestPreview;
