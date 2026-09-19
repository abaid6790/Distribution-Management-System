# Security Policy

## Supported version

Only the latest version of this codebase is supported. There is no
long-term-support branch — if you're running an older copy, update before
reporting an issue.

## Reporting a vulnerability

If you find a security issue, please **do not** open a public GitHub
issue. Instead, email [security@yourcompany.example] with:

- A description of the issue and its potential impact
- Steps to reproduce
- Any relevant logs or screenshots (redact real customer data)

You can expect an acknowledgement within a few days. Please give a
reasonable amount of time to fix an issue before disclosing it publicly.

## What's already implemented

- **Passwords** are hashed with Werkzeug's `generate_password_hash`
  (PBKDF2), never stored or logged in plaintext. Generated passwords for
  new users are shown exactly once on screen and are not retrievable
  afterward — only reset-able.
- **Sessions** use Flask-Login with signed, httpOnly cookies
  (`SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = "Lax"`).
- **SQL injection**: all queries go through SQLAlchemy's ORM/parameter
  binding — there is no raw string-interpolated SQL anywhere in the
  application code.
- **Access control**: every route is gated by a single, centrally
  enforced permission check (`app/permissions.py` +
  the `before_request` hook in `app/__init__.py`), rather than
  per-view checks that are easy to forget to add. Admin-only screens
  (Users, and anything not in the permission map) additionally require
  the `ADMIN` role explicitly.
- **No public registration** — accounts can only be created by an
  existing admin, from inside the authenticated app. There is no
  self-signup endpoint.
- **Forced credential rotation** for new accounts and password resets —
  a generated password cannot be used to access anything beyond the
  password-change screen until it's been replaced.
- **Last-admin protection** — the system will not allow the only active
  admin account to be demoted or deactivated, preventing accidental
  total lockout.
- **Audit trail** — create/update/delete/payment/adjustment/settings-
  change actions are recorded with the acting user and a timestamp
  (`audit_logs` table).

## Known gaps — read before a real production deployment

This is a working system, not a hardened one out of the box. Before
putting a client's real business data behind it:

1. **No CSRF protection yet.** Forms don't currently carry a CSRF token.
   Add `Flask-WTF`'s CSRF protection (or hand-roll tokens) before this
   is exposed to the public internet with real users. This is the single
   highest-priority item on this list.
2. **No login rate limiting.** There's nothing currently stopping
   repeated password-guessing attempts against `/login`. Add rate
   limiting (e.g. `Flask-Limiter`) or put the app behind a reverse proxy
   / WAF that provides it.
3. **`FLASK_DEBUG` must be `0` in production.** With debug mode on,
   an unhandled error shows a full interactive Python debugger to
   whoever triggered it — including the ability to execute arbitrary
   code. This is a Flask/Werkzeug behavior, not specific to this app,
   but it's worth stating explicitly: **never run a client-facing
   deployment with `FLASK_DEBUG=1`.**
4. **`SECRET_KEY` must be a long, random, unique value per deployment**
   — never reuse the development key, never commit it to version
   control. If it leaks, every session cookie and signed token becomes
   forgeable.
5. **Backup files are unencrypted JSON** containing full business data,
   including password hashes. Restrict filesystem permissions on the
   `backups/` directory, and treat downloaded backup files as sensitive
   — store and transmit them accordingly (e.g. don't email them
   unencrypted).
6. **No HTTPS by itself.** The app doesn't terminate TLS — that's the
   job of your reverse proxy (nginx, Caddy, or your PaaS). Never run a
   real deployment over plain HTTP; login credentials and session
   cookies would be sent in the clear.
7. **No field-level encryption at rest.** Customer/supplier contact
   details and financial figures are stored in plain columns. This is
   standard for this class of application, but be mindful of your
   client's data-protection obligations (e.g. local data protection law)
   when choosing where to host their database.
8. **Multi-tenancy is not implemented.** Never point two different
   clients at the same database — see `DEPLOYMENT.md`. There is
   currently no code-level tenant isolation to rely on.

## Recommended hardening checklist for a production rollout

- [ ] Add CSRF protection to all forms
- [ ] Add rate limiting to `/login`
- [ ] `FLASK_DEBUG=0`
- [ ] Unique, random `SECRET_KEY` (32+ bytes) per deployment
- [ ] HTTPS enforced (redirect HTTP → HTTPS at the proxy)
- [ ] Postgres not exposed to the public internet (bind to localhost or a
      private network; access only from the app server)
- [ ] Regular automated backups, stored somewhere other than the app
      server itself
- [ ] `backups/` directory permissions restricted to the app's service
      user only
- [ ] Dependencies kept up to date (`pip list --outdated`)
- [ ] A process supervisor (systemd, in `DEPLOYMENT.md`) so the app
      restarts automatically on crash or reboot
