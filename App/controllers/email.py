import mimetypes
import smtplib
import imaplib
from email.message import EmailMessage
from email.header import decode_header
from email.parser import BytesParser
from email.policy import default
from flask import current_app
from jinja2 import Template


def _cfg(key, default_value=None):
    return current_app.config.get(key, default_value)


def _bool_cfg(key, default_value=False):
    v = current_app.config.get(key, default_value)
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in ["1", "true", "yes", "on"]
    return bool(v)


def _decode_header_value(value):
    if not value:
        return ""
    parts = decode_header(value)
    out = []
    for part, enc in parts:
        if isinstance(part, bytes):
            out.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            out.append(str(part))
    return "".join(out)


def render_email_template(template_str, context=None):
    context = context or {}
    return Template(template_str).render(**context)


def send_email(
    to_email,
    subject,
    body_text=None,
    body_html=None,
    attachments=None,
    cc=None,
    bcc=None,
    reply_to=None,
    sender_email=None,
    sender_name=None
):
    if _bool_cfg("MAIL_SUPPRESS_SEND", False):
        return {"sent": False, "suppressed": True}

    mail_server = _cfg("MAIL_SERVER")
    mail_port = int(_cfg("MAIL_PORT", 587))
    mail_user = _cfg("MAIL_USERNAME")
    mail_pass = _cfg("MAIL_PASSWORD")
    use_tls = _bool_cfg("MAIL_USE_TLS", True)
    use_ssl = _bool_cfg("MAIL_USE_SSL", False)

    if not mail_server:
        raise ValueError("MAIL_SERVER is not configured")

    sender_email = sender_email or _cfg("MAIL_DEFAULT_SENDER") or mail_user
    sender_name = sender_name or _cfg("MAIL_FROM_NAME")

    if not sender_email:
        raise ValueError("MAIL_DEFAULT_SENDER (or MAIL_USERNAME) must be configured")

    msg = EmailMessage()

    if sender_name:
        msg["From"] = f"{sender_name} <{sender_email}>"
    else:
        msg["From"] = sender_email

    msg["To"] = to_email
    msg["Subject"] = subject

    if cc:
        msg["Cc"] = ", ".join(cc) if isinstance(cc, (list, tuple)) else str(cc)
    if reply_to:
        msg["Reply-To"] = reply_to

    if body_text and body_html:
        msg.set_content(body_text)
        msg.add_alternative(body_html, subtype="html")
    elif body_html:
        msg.add_alternative(body_html, subtype="html")
    else:
        msg.set_content(body_text or "")

    attachments = attachments or []
    for att in attachments:
        if isinstance(att, str):
            path = att
            ctype, _ = mimetypes.guess_type(path)
            maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
            with open(path, "rb") as f:
                data = f.read()
            filename = path.split("/")[-1]
            msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)
        elif isinstance(att, dict):
            filename = att.get("filename")
            data = att.get("data")
            content_type = att.get("content_type") or "application/octet-stream"
            if not filename or data is None:
                raise ValueError("Attachment dict must include filename and data")
            maintype, subtype = content_type.split("/", 1)
            msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)
        else:
            raise ValueError("Unsupported attachment type")

    recipients = [to_email]
    if cc:
        recipients += (cc if isinstance(cc, (list, tuple)) else [str(cc)])
    if bcc:
        recipients += (bcc if isinstance(bcc, (list, tuple)) else [str(bcc)])

    if use_ssl:
        server = smtplib.SMTP_SSL(mail_server, mail_port, timeout=20)
    else:
        server = smtplib.SMTP(mail_server, mail_port, timeout=20)

    try:
        if (not use_ssl) and use_tls:
            server.ehlo()
            server.starttls()
            server.ehlo()

        if mail_user and mail_pass:
            server.login(mail_user, mail_pass)

        server.send_message(msg, from_addr=sender_email, to_addrs=recipients)
    finally:
        try:
            server.quit()
        except Exception:
            pass

    return {"sent": True}


def send_templated_email(
    to_email,
    subject_template,
    body_template,
    context=None,
    body_html_template=None,
    attachments=None,
    cc=None,
    bcc=None,
    reply_to=None
):
    context = context or {}
    subject = render_email_template(subject_template, context)
    body_text = render_email_template(body_template, context) if body_template else None
    body_html = render_email_template(body_html_template, context) if body_html_template else None
    return send_email(
        to_email=to_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        attachments=attachments,
        cc=cc,
        bcc=bcc,
        reply_to=reply_to
    )


def _imap_connect():
    host = _cfg("IMAP_SERVER")
    port = int(_cfg("IMAP_PORT", 993))
    user = _cfg("IMAP_USERNAME")
    password = _cfg("IMAP_PASSWORD")
    use_ssl = _bool_cfg("IMAP_USE_SSL", True)

    if not host or not user or not password:
        raise ValueError("IMAP_SERVER, IMAP_USERNAME, IMAP_PASSWORD must be configured")

    if use_ssl:
        imap = imaplib.IMAP4_SSL(host, port)
    else:
        imap = imaplib.IMAP4(host, port)

    imap.login(user, password)
    return imap


def list_inbox_emails(limit=20, folder="INBOX", search_criteria="ALL"):
    limit = int(limit) if limit else 20
    imap = _imap_connect()
    try:
        imap.select(folder)
        status, data = imap.search(None, search_criteria)
        if status != "OK":
            return []

        ids = data[0].split()
        ids = ids[-limit:] if limit > 0 else ids

        results = []
        for uid in reversed(ids):
            status, msg_data = imap.fetch(uid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)] BODY.PEEK[TEXT]<0.512>)")
            if status != "OK" or not msg_data:
                continue

            header_bytes = b""
            snippet_bytes = b""
            for item in msg_data:
                if isinstance(item, tuple) and b"HEADER.FIELDS" in item[0]:
                    header_bytes = item[1] or b""
                if isinstance(item, tuple) and b"BODY[TEXT]" in item[0]:
                    snippet_bytes = item[1] or b""

            headers = BytesParser(policy=default).parsebytes(header_bytes)
            from_v = _decode_header_value(headers.get("From"))
            subject_v = _decode_header_value(headers.get("Subject"))
            date_v = _decode_header_value(headers.get("Date"))
            snippet_v = snippet_bytes.decode("utf-8", errors="replace").strip()

            results.append({
                "uid": uid.decode("utf-8", errors="replace"),
                "from": from_v,
                "subject": subject_v,
                "date": date_v,
                "snippet": snippet_v
            })

        return results
    finally:
        try:
            imap.logout()
        except Exception:
            pass


def get_email_by_uid(uid, folder="INBOX"):
    if isinstance(uid, str):
        uid_b = uid.encode("utf-8")
    else:
        uid_b = uid

    imap = _imap_connect()
    try:
        imap.select(folder)
        status, msg_data = imap.fetch(uid_b, "(RFC822)")
        if status != "OK" or not msg_data:
            return None

        raw = None
        for item in msg_data:
            if isinstance(item, tuple):
                raw = item[1]
                break
        if not raw:
            return None

        msg = BytesParser(policy=default).parsebytes(raw)
        from_v = _decode_header_value(msg.get("From"))
        to_v = _decode_header_value(msg.get("To"))
        subject_v = _decode_header_value(msg.get("Subject"))
        date_v = _decode_header_value(msg.get("Date"))

        body_text = _extract_text(msg)

        return {
            "uid": uid if isinstance(uid, str) else uid.decode("utf-8", errors="replace"),
            "from": from_v,
            "to": to_v,
            "subject": subject_v,
            "date": date_v,
            "body": body_text
        }
    finally:
        try:
            imap.logout()
        except Exception:
            pass


def _extract_text(msg):
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = part.get("Content-Disposition", "")
            if ctype == "text/plain" and "attachment" not in disp.lower():
                return part.get_content().strip()
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = part.get("Content-Disposition", "")
            if ctype == "text/html" and "attachment" not in disp.lower():
                return part.get_content().strip()
        return ""
    return (msg.get_content() or "").strip()