import { useRef, useEffect } from 'react';
import './DigestPreview.css';

const DigestPreview = ({ 
  digestContent, 
  isLoading = false, 
  error = null 
}) => {
  const iframeRef = useRef(null);

  // Update iframe content when digestContent changes
  useEffect(() => {
    if (iframeRef.current && digestContent) {
      const iframe = iframeRef.current;
      const doc = iframe.contentDocument || iframe.contentWindow.document;
      
      // Use digestContent directly without any sanitization
      const fullHtml = digestContent;
      
      doc.open();
      doc.write(fullHtml);
      doc.close();
      
      // Ensure white background for the document
      if (doc.body) {
        doc.body.style.backgroundColor = '#ffffff';
      }
      
      // Ensure all links open in new tab/window
      const links = doc.querySelectorAll('a');
      links.forEach(link => {
        link.setAttribute('target', '_blank');
        link.setAttribute('rel', 'noopener noreferrer');
      });
    }
  }, [digestContent]);

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
