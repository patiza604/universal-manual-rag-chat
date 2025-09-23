# Security Policy

## Supported Versions

We actively support and provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of Universal Manual RAG Chat seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please send an email to: **security@universal-rag-chat.com**

Include the following information in your report:
- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

### What to Expect

After submitting a report, you can expect:

1. **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 48 hours
2. **Initial Assessment**: We will provide an initial assessment within 5 business days
3. **Progress Updates**: We will keep you informed of our progress throughout the investigation
4. **Resolution Timeline**: We aim to resolve critical vulnerabilities within 7 days, high severity within 14 days, and medium/low severity within 30 days

### Security Update Process

1. **Verification**: Our security team will verify and reproduce the vulnerability
2. **Impact Assessment**: We will assess the impact and assign a severity level
3. **Fix Development**: We will develop and test a fix for the vulnerability
4. **Coordinated Disclosure**: We will coordinate the release of the fix with the reporter
5. **Public Disclosure**: After the fix is deployed, we will publicly disclose the vulnerability details

## Security Best Practices

### For Developers

- **Authentication**: Always use secure authentication methods (Firebase Auth, OAuth 2.0)
- **API Security**: Implement proper rate limiting and input validation
- **Data Protection**: Never log or expose sensitive data (API keys, user tokens)
- **Dependency Management**: Keep all dependencies updated and scan for vulnerabilities
- **Code Review**: All security-related changes require peer review

### For Deployment

- **Environment Variables**: Store sensitive configuration in environment variables
- **HTTPS**: Always use HTTPS in production environments
- **Access Control**: Implement least-privilege access principles
- **Monitoring**: Enable security monitoring and alerting
- **Backup**: Maintain secure, encrypted backups

### For Users

- **Account Security**: Use strong, unique passwords and enable 2FA when available
- **Data Privacy**: Review and understand data collection and usage policies
- **Updates**: Keep the application updated to the latest version
- **Reporting**: Report any suspicious activity or potential security issues

## Known Security Considerations

### Current Implementation

- **Firebase Authentication**: Secure user authentication with Google Sign-In
- **API Rate Limiting**: Implemented to prevent abuse
- **CORS Configuration**: Properly configured for production domains
- **Service Account Security**: Firebase service accounts use least-privilege access
- **Input Validation**: All user inputs are validated and sanitized
- **Image Security**: Secure image handling with Firebase Storage and signed URLs

### Data Handling

- **Chat Data**: User chat conversations are stored securely in Firebase Firestore
- **Voice Data**: Speech-to-text processing uses Google Cloud Speech API with secure transmission
- **Manual Content**: RAG system only uses official manual content (no external data sources)
- **Analytics**: Limited telemetry collection with user privacy protection

### Infrastructure Security

- **Google Cloud Platform**: Leverages GCP's enterprise-grade security
- **Cloud Run**: Secure containerized deployment with automatic HTTPS
- **Firebase**: Enterprise-grade security and compliance (SOC 1, SOC 2, ISO 27001)
- **Network Security**: Traffic encryption in transit and at rest

## Security Resources

- [Google Cloud Security Best Practices](https://cloud.google.com/security/best-practices)
- [Firebase Security Documentation](https://firebase.google.com/docs/rules)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flutter Security Best Practices](https://docs.flutter.dev/security)

## Compliance

This project follows security practices aligned with:
- **OWASP Application Security Verification Standard (ASVS)**
- **Google Cloud Security Command Center recommendations**
- **Firebase Security Rules best practices**
- **General Data Protection Regulation (GDPR) principles**

## Contact

For general security questions or concerns, you can reach out to:
- **Security Team**: security@universal-rag-chat.com
- **Project Maintainers**: See [CONTRIBUTING.md](CONTRIBUTING.md) for contact information

---

**Last Updated**: September 23, 2025
**Next Review**: December 23, 2025