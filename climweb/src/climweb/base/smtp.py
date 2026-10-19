"""
Outgoing email (SMTP) configured from the CMS.

Settings -> Email lets a superuser enter the SMTP server, account and sender
address in the browser, so a country no longer needs server access (or a
docker-compose change) to set up or fix email. The password is stored encrypted
with the same key as the backup credentials (see ``backups/crypto.py``).

``SiteSMTPBackend`` is the production ``EMAIL_BACKEND``. Every email the site
sends goes through it — form notifications, password resets, 2FA codes, Wagtail
moderation emails — so none of the sending code needs to know where the
configuration comes from:

  * CMS settings switched on  -> use them, and send everything from the
    configured sender address (providers such as Gmail and Microsoft 365 only
    accept the address of the account you sign in with).
  * otherwise                 -> the EMAIL_* environment variables, as before.

If the CMS settings ever lock people out (for example the 2FA email fallback
stops working), ``manage.py disable_cms_email`` switches back to the
environment variables.
"""
import smtplib
import socket
import ssl
from dataclasses import dataclass
from email.utils import formataddr

from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend
from django.db import DatabaseError
from django.utils.translation import gettext as _
from loguru import logger

# Seconds to wait for the mail server. Django's default is to wait forever,
# which would hang a page (e.g. a form submission) on an unreachable server.
DEFAULT_TIMEOUT = 20


class Security:
    STARTTLS = "starttls"
    SSL = "ssl"
    NONE = "none"


# host, port, security for each provider preset. "custom" has none.
PROVIDER_PRESETS = {
    "gmail": ("smtp.gmail.com", 587, Security.STARTTLS),
    "microsoft": ("smtp.office365.com", 587, Security.STARTTLS),
}


@dataclass
class SMTPConfig:
    host: str
    port: int
    security: str
    username: str = ""
    password: str = ""
    from_email: str = ""
    from_name: str = ""
    timeout: int = DEFAULT_TIMEOUT

    @property
    def use_tls(self):
        return self.security == Security.STARTTLS

    @property
    def use_ssl(self):
        return self.security == Security.SSL

    @property
    def sender(self):
        if not self.from_email:
            return ""
        if self.from_name:
            return formataddr((self.from_name, self.from_email))
        return self.from_email

    def connection(self, fail_silently=False):
        """A plain SMTP connection for exactly this configuration."""
        return SMTPEmailBackend(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            use_tls=self.use_tls,
            use_ssl=self.use_ssl,
            timeout=self.timeout,
            fail_silently=fail_silently,
        )


def get_active_config():
    """The CMS email configuration, or None to use the environment variables.

    Never raises: a missing table (before migrating), an undecryptable password
    (SECRET_KEY rotated) or an incomplete form all fall back to the environment
    so that email keeps working.
    """
    from climweb.base.models.email_settings import EmailSettings

    try:
        email_settings = EmailSettings.load()
    except DatabaseError:
        return None

    if not email_settings.enabled:
        return None

    try:
        return email_settings.get_config()
    except Exception as e:
        logger.warning(f"[EMAIL] CMS email settings unusable, using server settings instead: {e!r}")
        return None


class SiteSMTPBackend(SMTPEmailBackend):
    """SMTP backend that prefers the CMS email settings over the environment."""

    def __init__(self, host=None, port=None, username=None, password=None,
                 use_tls=None, fail_silently=False, use_ssl=None, timeout=None,
                 **kwargs):
        self.cms_config = get_active_config()
        config = self.cms_config
        if config:
            host = host or config.host
            port = port or config.port
            username = config.username if username is None else username
            password = config.password if password is None else password
            if use_tls is None and use_ssl is None:
                use_tls, use_ssl = config.use_tls, config.use_ssl
            timeout = config.timeout if timeout is None else timeout

        super().__init__(host=host, port=port, username=username, password=password,
                         use_tls=use_tls, fail_silently=fail_silently, use_ssl=use_ssl,
                         timeout=timeout, **kwargs)

    def send_messages(self, email_messages):
        sender = self.cms_config.sender if self.cms_config else ""
        if sender and email_messages:
            for message in email_messages:
                message.from_email = sender
        return super().send_messages(email_messages)


def friendly_error(exc):
    """Explain an SMTP failure in words a site administrator can act on."""
    detail = str(exc) or exc.__class__.__name__
    if isinstance(exc, smtplib.SMTPResponseException) and isinstance(exc.smtp_error, bytes):
        detail = f"{exc.smtp_code} {exc.smtp_error.decode('utf-8', 'replace')}"
    text = detail.lower()

    if "5.7.139" in text or "smtpclientauthentication is disabled" in text \
            or "basic authentication is disabled" in text:
        message = _(
            "Microsoft 365 refused to sign in. SMTP AUTH is turned off for this "
            "mailbox or organisation, or Microsoft no longer accepts passwords "
            "(including app passwords) for it. Ask your IT administrator to "
            "enable SMTP AUTH for this mailbox, or use a different provider."
        )
    elif "5.7.9" in text or "application-specific password" in text:
        message = _(
            "Gmail needs an App Password, not the normal account password. Turn "
            "on 2-Step Verification for the Google account, create an App "
            "Password, and paste it here."
        )
    elif "sendasdenied" in text or "5.7.60" in text or "not allowed to send as" in text:
        message = _(
            "The mail server will not send from this sender address. Use the "
            "address of the account you sign in with, or an alias that account "
            "is allowed to send as."
        )
    elif isinstance(exc, smtplib.SMTPAuthenticationError):
        message = _(
            "The username or password was not accepted. Check both. Gmail and "
            "Microsoft 365 accounts with 2-step verification need an app "
            "password instead of the normal password."
        )
    elif isinstance(exc, smtplib.SMTPNotSupportedError) or "starttls extension not supported" in text:
        message = _(
            "The server does not support this security setting. Try SSL/TLS on "
            "port 465, or STARTTLS on port 587."
        )
    elif isinstance(exc, ssl.SSLError):
        message = _(
            "A secure connection could not be set up. Port 465 normally needs "
            "SSL/TLS and port 587 needs STARTTLS. Check the security setting "
            "matches the port."
        )
    elif isinstance(exc, socket.gaierror):
        message = _("The server name could not be found. Check the host name.")
    elif isinstance(exc, (socket.timeout, TimeoutError, ConnectionError, OSError)) \
            and not isinstance(exc, smtplib.SMTPException):
        message = _(
            "Could not reach the mail server. Check the host and port. A "
            "firewall at your hosting provider may also be blocking outgoing "
            "email ports."
        )
    elif isinstance(exc, smtplib.SMTPRecipientsRefused):
        message = _("The server refused to deliver to the test address.")
    elif isinstance(exc, smtplib.SMTPSenderRefused):
        message = _(
            "The server refused the sender address. Use the address of the "
            "account you sign in with."
        )
    else:
        message = _("The test email could not be sent.")

    return _("%(message)s (Details: %(detail)s)") % {"message": message, "detail": detail}
