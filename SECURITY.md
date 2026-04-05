# 🔒 Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| UIv0.3  | ✅        |
| < 0.3   | ❌        |

## Reporting a Vulnerability

If you discover a security vulnerability in MAGGxDND:

1. **Do NOT** open a public issue
2. Email the project maintainers with details
3. Include steps to reproduce the vulnerability
4. We will acknowledge receipt within **48 hours**
5. We will provide a full response within **7 days**

## What to Expect

- We will confirm the vulnerability and assign a severity
- We will work on a fix and notify you when it's ready
- We will credit you in the release notes (if you wish)

## Security Best Practices for Contributors

- Never commit `.env` files with real secrets
- Never commit API keys, tokens, or passwords
- Use environment variables for sensitive data
- Validate and sanitize all user input
- Use parameterized queries (SQLAlchemy handles this)
- Review CORS configuration changes carefully

---

<div align="center">

Security matters — keep the dragons safe! 🐉🛡️

</div>
