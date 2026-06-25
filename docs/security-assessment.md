# Security Assessment

[< Back to Overview](../SAVANT.md)

---

## Vulnerability Summary

| Finding | Severity | Location |
|---------|----------|----------|
| No certificate pinning | HIGH | `SavantServiceFactory.java` |
| Trust-all SSL on local network | MEDIUM | `SavantSSLHelper.java` |
| Password stored in plaintext | HIGH | `SavantUser.java` |
| Hardcoded API keys | MEDIUM | `DynamicCloudConfig.java` |
| Custom HMAC auth (not standard JWT) | LOW | `SavantRestUtils.java` |
| Optional cleartext connections | MEDIUM | Connection specs allow non-TLS |

---

## Certificate Pinning

**Status: NOT IMPLEMENTED**

- No `CertificatePinner.Builder` usage found
- No `sha256/` pin hashes in active code
- No `network_security_config.xml` pins
- Default TrustManager instances with empty pin sets

---

## SSL/TLS Configuration

**Local connections:**
- `SavantSSLHelper.java` implements `X509TrustManager` that **trusts all certificates**
- `HostnameVerifier` always returns true
- Self-signed certificates accepted without validation

**Cloud connections:**
- Uses MODERN_TLS `ConnectionSpec`
- Optional CLEARTEXT also allowed
- No certificate pinning

---

## Credential Storage

- Cloud user credentials stored in **SharedPreferences** (unencrypted)
- Fields stored: email, **password (plaintext)**, token, secret
- `SavantUser` object retains password field for auto-re-authentication

---

## MITM Feasibility

**Cloud traffic:** Standard HTTPS proxy with user-installed CA certificate will intercept all cloud traffic. No pinning to bypass.

**Local WebSocket traffic:** Trust-all SSL means any certificate is accepted. Interception is trivial on the same network without any additional tools (no Frida/objection needed).

**Recommended setup:**
1. Connect to same WiFi network as Savant host
2. Run mitmproxy/Charles/Burp as transparent proxy
3. For cloud: Install proxy CA on device
4. For local: No additional steps needed (trust-all)

---

## Hardcoded Secrets

### API Keys

| Environment | Key |
|-------------|-----|
| RELEASE | `FoWT9Z40axK88bO95EbNVfDILm34ff` |
| ALPHA | `JUa0aq5MT8zaJ93mIpCo9oXItFUO5y` |
| BETA | `7tLg9qUXt135v6389kMOivkqsbx1W6` |
| DEV2 | `Nmch38eg4eOy8bWLdXFmPaLY482w1P` |

### Cloud URLs

All environment URLs hardcoded (see [Cloud API](cloud-api.md)).

---

## Authentication Scheme

Custom HMAC-SHA256 rather than standard JWT/OAuth2. While functional, this means:
- No standard token expiry semantics
- No standard token revocation
- Custom implementation may have undiscovered vulnerabilities
- Replay attacks possible within timestamp window if HMAC is reused

See [Authentication](authentication.md) for full details.
