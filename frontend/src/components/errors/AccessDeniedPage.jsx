/**
 * Access Denied Page Component
 * Specialized error page for access denied scenarios
 */
import React, { useState } from 'react';

/**
 * Access denied error page component
 * @param {Object} props - Component props
 * @param {string} props.token - Token that was denied (optional)
 * @param {string} props.reason - Specific reason for denial (optional)
 * @param {Function} props.onGoHome - Go home callback (optional)
 * @returns {JSX.Element} Access denied page
 */
function AccessDeniedPage({ token = null, reason = null, onGoHome = null }) {
  const [showTroubleshooting, setShowTroubleshooting] = useState(false);

  const handleContactSupport = () => {
    // In a real app, this might open a contact form or email client
    window.location.href = 'mailto:suporte@dailyscribe.com.br?subject=Problema de Acesso - Token Negado';
  };

  const handleShowTroubleshooting = () => {
    setShowTroubleshooting(true);
  };

  // Get specific reason details
  const getReasonDetails = () => {
    const reasonMap = {
      'DEVICE_MISMATCH': {
        title: 'Dispositivo Diferente',
        description: 'Este link foi criado para ser usado em outro dispositivo.',
        icon: '📱',
        solutions: [
          'Acesse pelo dispositivo onde solicitou o digest',
          'Use o mesmo navegador que utilizou para se inscrever',
          'Verifique se está logado na mesma conta de email',
        ]
      },
      'LOCATION_MISMATCH': {
        title: 'Localização Diferente',
        description: 'Por segurança, detectamos acesso de uma localização incomum.',
        icon: '🌍',
        solutions: [
          'Acesse pelo local onde costuma ler os digests',
          'Desative VPN se estiver usando',
          'Use sua conexão de internet habitual',
        ]
      },
      'TOKEN_USED_UP': {
        title: 'Token Esgotado',
        description: 'Este link já foi usado o máximo de vezes permitido (10 usos).',
        icon: '🔄',
        solutions: [
          'Solicite um novo digest para obter novo link',
          'Salve suas configurações antes de sair da página',
          'Use o link apenas quando necessário',
        ]
      },
      'INSUFFICIENT_PERMISSIONS': {
        title: 'Permissões Insuficientes',
        description: 'Este token não tem as permissões necessárias.',
        icon: '🔑',
        solutions: [
          'Verifique se está usando o link correto do email',
          'Use o link mais recente recebido',
          'Confirme que o email não foi encaminhado',
        ]
      },
    };

    return reasonMap[reason] || {
      title: 'Acesso Não Autorizado',
      description: 'Não foi possível autorizar o acesso a esta página.',
      icon: '🔒',
      solutions: [
        'Verifique se está usando o link correto',
        'Tente usar o link original do email',
        'Solicite um novo digest se necessário',
      ]
    };
  };

  const reasonDetails = getReasonDetails();

  return (
    <div className="preference-page">
      <div className="preference-container">
        <div className="preference-header">
          <h1>Preferências</h1>
        </div>

        <div className="error-page">
          <div className="error-icon" role="img" aria-label="Acesso negado">
            {reasonDetails.icon}
          </div>

          <h2>Acesso Negado</h2>
          
          <p className="error-message">
            {reasonDetails.title}
          </p>

          <p className="error-description">
            {reasonDetails.description}
          </p>

          {!showTroubleshooting && (
            <div className="quick-solutions">
              <h3>Soluções rápidas:</h3>
              
              <div className="solution-list">
                {reasonDetails.solutions.slice(0, 2).map((solution, index) => (
                  <div key={index} className="solution-item">
                    <span className="solution-number">{index + 1}</span>
                    <span className="solution-text">{solution}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {showTroubleshooting && (
            <div className="troubleshooting-guide">
              <h3>Guia de Solução de Problemas</h3>
              
              <div className="troubleshooting-content">
                <h4>✅ Verificações Básicas:</h4>
                <div className="checklist">
                  {reasonDetails.solutions.map((solution, index) => (
                    <label key={index} className="checklist-item">
                      <input type="checkbox" />
                      <span className="checkmark"></span>
                      <span className="checklist-text">{solution}</span>
                    </label>
                  ))}
                </div>

                <h4>🔧 Verificações Técnicas:</h4>
                <div className="technical-checks">
                  <div className="check-item">
                    <strong>Navegador:</strong> Tente usar um navegador diferente
                  </div>
                  <div className="check-item">
                    <strong>Cookies:</strong> Verifique se os cookies estão habilitados
                  </div>
                  <div className="check-item">
                    <strong>Cache:</strong> Limpe o cache do navegador
                  </div>
                  <div className="check-item">
                    <strong>JavaScript:</strong> Confirme que o JavaScript está ativo
                  </div>
                </div>

                <h4>🛡️ Configurações de Segurança:</h4>
                <div className="security-info">
                  <p>
                    O Daily Scribe usa várias camadas de segurança para proteger 
                    suas preferências:
                  </p>
                  <ul>
                    <li>Tokens vinculados ao dispositivo e localização</li>
                    <li>Limite de tentativas de acesso</li>
                    <li>Verificação de integridade do link</li>
                    <li>Monitoramento de atividade suspeita</li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          <div className="error-actions">
            <button 
              className="btn btn-outline"
              onClick={handleContactSupport}
              aria-label="Entrar em contato com o suporte"
            >
              <span className="btn-icon">📞</span>
              Suporte
            </button>

            {!showTroubleshooting && (
              <button 
                className="btn btn-text"
                onClick={handleShowTroubleshooting}
                aria-label="Ver guia de solução de problemas"
              >
                <span className="btn-icon">🔧</span>
                Solução de Problemas
              </button>
            )}
          </div>

          {/* Security notice */}
          <div className="security-notice">
            <h4>🛡️ Sobre a Segurança:</h4>
            <p>
              Estas verificações protegem suas preferências contra acesso não autorizado. 
              Se você é o proprietário legítimo desta conta, as soluções acima devem resolver o problema.
            </p>
          </div>

          {/* Technical details for debugging (only in development) */}
          {process.env.NODE_ENV === 'development' && (
            <details className="error-debug">
              <summary>Detalhes de Acesso (Dev)</summary>
              <pre>{JSON.stringify({
                reason,
                tokenLength: token?.length || 0,
                userAgent: navigator.userAgent,
                timestamp: new Date().toISOString(),
                referrer: document.referrer,
              }, null, 2)}</pre>
            </details>
          )}
        </div>

        <div className="preference-footer">
          <p className="footer-note">
            <strong>Ainda com problemas?</strong> Nossa equipe de suporte está pronta para ajudar.
          </p>
          <p className="footer-security">
            Reporte problemas de acesso para melhorarmos a segurança.
          </p>
        </div>
      </div>
    </div>
  );
}

export default AccessDeniedPage;
