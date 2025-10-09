import React from 'react';

const ComplianceBanner = () => {
  return (
    <div className="compliance-banner">
      <div className="badge">🔐 HIPAA Compliant</div>
      <div className="badge">🛡️ GDPR Ready</div>
      <div className="badge">♿ WCAG 2.1 AA</div>
      <p className="disclaimer">
        AI recommendations are for informational purposes only. Always consult a licensed physician.
      </p>
    </div>
  );
};

export default ComplianceBanner;