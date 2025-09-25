# Security Setup Guide

## 🔐 Service Account Credentials

### Production Deployment (Recommended)
Use **Application Default Credentials** for maximum security:
1. Deploy to Google Cloud Run with proper IAM roles
2. No credential files needed - uses the runtime's default service account
3. Most secure option with automatic credential rotation

### Local Development
Use environment variables:
1. Copy `.env.example` to `.env`
2. Set `GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json`
3. Keep credentials outside the repository

### ⚠️ NEVER COMMIT CREDENTIALS
- Service account JSON files must NEVER be committed to git
- Use environment variables or Application Default Credentials
- Keep all credentials in `.gitignore`

## 🚨 If Credentials Were Exposed
If service account keys were ever committed to git:
1. **Rotate the keys immediately** in Google Cloud Console
2. **Remove from git history**: `git filter-branch --tree-filter 'rm -rf gcp-keys' HEAD`
3. **Update all deployments** with new credentials
4. **Monitor for unauthorized usage** in Cloud Console

## 🔒 Security Best Practices
1. Use least privilege principle for IAM roles
2. Enable audit logging for all services
3. Rotate credentials regularly
4. Use Cloud KMS for additional encryption
5. Implement proper CORS policies
6. Add rate limiting to APIs
7. Validate all inputs
8. Use HTTPS only

## 📋 Environment Variables Required
See `.env.example` for complete list of required environment variables.