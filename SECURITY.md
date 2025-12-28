# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in the SunGather charm, please report it responsibly.

### How to Report

Please report security vulnerabilities using GitHub's Security Advisory feature:

1. Go to the repository's Security tab
2. Click on "Report a vulnerability"
3. Fill in the details of the vulnerability

Alternatively, if you prefer not to use GitHub's system, you can open a private security advisory or contact the maintainers directly.

### What to Include

When reporting a security vulnerability, please include:

- A description of the vulnerability
- Steps to reproduce the issue
- Potential impact of the vulnerability
- Any suggested fixes (if applicable)

### Response Timeline

- We will acknowledge receipt of your vulnerability report within 48 hours
- We will provide an initial assessment within 5 business days
- We will work with you to understand and validate the vulnerability
- We will develop and test a fix
- We will coordinate disclosure timing with you

### Disclosure Policy

- Please do not publicly disclose the vulnerability until we have had a chance to address it
- We aim to release security fixes within 30 days of validation
- We will credit you in the security advisory (unless you prefer to remain anonymous)

## Supported Versions

We support the latest stable release with security updates. Older versions may receive critical security fixes on a case-by-case basis.

## Security Best Practises

When deploying the SunGather charm:

1. **Use Juju secrets** for all sensitive credentials (MQTT passwords, InfluxDB tokens, PVOutput API keys)
2. **Network security**: Ensure your inverter is on a secure network segment
3. **Access control**: Limit access to the Juju controller and models
4. **Updates**: Keep the charm and the SunGather OCI image up to date
5. **Ingress**: When exposing the web interface, use TLS and authentication

## Known Security Considerations

- The charm requires network access to the solar inverter
- Secrets are managed through Juju's secret management system
- The web interface does not include built-in authentication (use ingress with authentication if exposing externally)

## Contact

For non-security issues, please use the GitHub issue tracker.
