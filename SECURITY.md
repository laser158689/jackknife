# Security Policy

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Report privately via [GitHub's private vulnerability reporting](https://github.com/laser158689/jackknife/security/advisories/new).

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

You'll receive a response within 7 days.

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x | Yes |

## Security considerations

- **Never commit secrets** — use `.env` for API keys and credentials; `.env` is in `.gitignore`
- **Absolute paths only** — `jackknife` rejects relative paths in config to prevent path traversal
- **Optional extras** — only install the blades you need to minimize attack surface
