/**
 * Expired Token Page Component
 * Specialized error page for expired tokens with specific messaging and actions
 */
import React, { useState } from 'react';

/**
 * Expired token error page component
 * @param {Object} props - Component props
 * @param {string} props.token - Expired token (optional)
 * @param {Object} props.tokenInfo - Token information if available (optional)
 * @param {Function} props.onGoHome - Go home callback (optional)
 * @returns {JSX.Element} Expired token page
 */
function ExpiredTokenPage({ token = null, tokenInfo = null, onGoHome = null }) {
  const [showDetails, setShowDetails] = useState(false);

  const handleLearnMore = () => {
    setShowDetails(true);
  };

  // Calculate how long ago the token expired (if we have that info)
  const getExpirationInfo = () => {
    if (!tokenInfo?.expiresAt) {
      return null;
    }

    const now = new Date();
    const expiredAt = new Date(tokenInfo.expiresAt);
    const hoursAgo = Math.floor((now - expiredAt) / (1000 * 60 * 60));
    const daysAgo = Math.floor(hoursAgo / 24);

    if (daysAgo > 0) {
      return `Expirou há ${daysAgo} dia${daysAgo > 1 ? 's' : ''}`;
    } else if (hoursAgo > 0) {
      return `Expirou há ${hoursAgo} hora${hoursAgo > 1 ? 's' : ''}`;
    } else {
      return 'Expirou recentemente';
    }
  };

  const expirationInfo = getExpirationInfo();

  return (
    <div className="preference-page">
      <div className="preference-container">
        <div className="preference-header">
          <h1>Preferências</h1>
        </div>

        <div className="error-page">
          <div className="error-icon" role="img" aria-label="Token expirado">
            ⏰
          </div>

          <h2>Token Expirado</h2>
          
          <p className="error-message">
            Este link de configuração já expirou.
          </p>

          <p className="error-description">
            Por motivos de segurança, os links de configuração têm validade de 24 horas.
            {expirationInfo && (
              <span className="expiration-info">
                <br /><em>{expirationInfo}</em>
              </span>
            )}
          </p>

          {!showDetails && (
            <div className="quick-actions">
              <h3>O que você pode fazer:</h3>
              
              <div className="action-list">
                <div className="action-item">
                  <span className="action-icon">📧</span>
                  <div className="action-content">
                    <strong>Solicitar novo digest</strong>
                    <p>Receba um novo email com link atualizado</p>
                  </div>
                </div>
                
                <div className="action-item">
                  <span className="action-icon">⚙️</span>
                  <div className="action-content">
                    <strong>Suas preferências atuais</strong>
                    <p>Continuam ativas mesmo com link expirado</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {showDetails && (
            <div className="detailed-explanation">
              <h3>Por que os tokens expiram?</h3>
              
              <div className="explanation-content">
                <div className="explanation-item">
                  <h4>🔒 Segurança</h4>
                  <p>Links temporários protegem suas configurações contra acesso não autorizado.</p>
                </div>
                
                <div className="explanation-item">
                  <h4>🛡️ Privacidade</h4>
                  <p>Tokens com validade limitada reduzem riscos se o link for compartilhado acidentalmente.</p>
                </div>
                
                <div className="explanation-item">
                  <h4>⚡ Performance</h4>
                  <p>Limpeza automática de tokens mantém o sistema eficiente.</p>
                </div>
              </div>

              <div className="security-notice">
                <h4>📋 Detalhes de Segurança:</h4>
                <ul>
                  <li>Validade: 24 horas após criação</li>
                  <li>Limite de uso: 10 acessos por token</li>
                  <li>Vinculação: Token vinculado ao dispositivo de origem</li>
                  <li>Renovação: Automática a cada novo digest</li>
                </ul>
              </div>
            </div>
          )}

          <div className="error-actions">
            {!showDetails && (
              <button 
                className="btn btn-text"
                onClick={handleLearnMore}
                aria-label="Saber mais sobre expiração de tokens"
              >
                <span className="btn-icon">ℹ️</span>
                Saber Mais
              </button>
            )}
          </div>

          {/* Helpful tips */}
          <div className="tips-section">
            <h4>💡 Dica:</h4>
            <p>
              Salve o Daily Scribe nos seus favoritos para acessar facilmente 
              e sempre ter links atualizados nos seus emails.
            </p>
          </div>

          {/* Technical details for debugging (only in development) */}
          {process.env.NODE_ENV === 'development' && tokenInfo && (
            <details className="error-debug">
              <summary>Informações do Token (Dev)</summary>
              <pre>{JSON.stringify({
                expiresAt: tokenInfo.expiresAt,
                issuedAt: tokenInfo.issuedAt,
                tokenLength: token?.length || 0,
                hoursExpired: tokenInfo.expiresAt ? 
                  Math.floor((new Date() - new Date(tokenInfo.expiresAt)) / (1000 * 60 * 60)) : 
                  null,
              }, null, 2)}</pre>
            </details>
          )}
        </div>

        <div className="preference-footer">
          <p className="footer-note">
            <strong>Suas preferências foram salvas</strong> e continuam ativas.
          </p>
          <p className="footer-security">
            Novos digests incluirão automaticamente um link atualizado.
          </p>
        </div>
      </div>
    </div>
  );
}

export default ExpiredTokenPage;
