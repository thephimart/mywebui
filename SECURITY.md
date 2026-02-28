# Security Policy

## Overview

`mywebui` is a **local-first system** designed to run inside a trusted boundary
(e.g. a developer workstation, VM, or private server).

Security is treated as a **first-class design constraint**, not an afterthought.
However, this project is currently in **alpha** and should not yet be considered
production-hardened.

---

## Supported Versions

Only the **latest tagged alpha release** is supported for security review.

- Older alpha tags may contain known or unknown issues
- No security backports are provided before beta

---

## Threat Model

`mywebui` assumes:
- The host machine is trusted
- The operator controls local access
- No hostile multi-tenant environment
- No exposure directly to the public internet

**Out of scope (by design):**
- Cloud threat models
- Zero-trust internal networking
- Malicious local administrators
- Compromised host OS

This is a deliberate design choice, not an oversight.

---

## Reporting a Vulnerability

If you discover a security issue, please **do not open a public issue**.

Instead, report it privately via one of the following:

- GitHub Security Advisories (preferred)
- Email: **security@phimart.consulting**

Please include:
- A clear description of the issue
- Steps to reproduce (if applicable)
- Potential impact
- Affected versions or commit hash

---

## Disclosure Policy

- Valid reports will be acknowledged within **72 hours**
- Fixes will be developed privately
- Public disclosure will occur **after a fix is available**
- Credit will be given if requested

---

## Current Security Guarantees

Within the alpha scope, the project guarantees:
- Explicit authentication and authorization boundaries
- No silent tool execution
- Auditable side-effects
- No background network access without configuration
- No telemetry or data exfiltration

These guarantees are enforced by design and covered by tests where applicable.

---

## Alpha Caveat

This project is **not yet suitable for high-risk or production environments**.

If you require:
- Strong sandboxing
- Hostile multi-user guarantees
- Remote exposure hardening
- Formal security audits

Please wait for beta or contribute to the hardening effort.

---

## Acknowledgements

Security researchers and contributors who help improve the project
will be credited unless they prefer anonymity.

Thank you for helping keep `mywebui` safe.
