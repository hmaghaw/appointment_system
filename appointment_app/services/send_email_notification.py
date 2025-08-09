from inspect import signature
from n8n_email_client import EmailClient
from email_message import EmailMessage  # has methods like user_signed_up(), email_verification(), etc.

def send_email_notification(trigger_event: str, to: str, **kwargs):
    """
    Call the EmailMessage method named by trigger_event with **kwargs
    and send the resulting email.
    """
    email_client = EmailClient()
    notification = EmailMessage()

    # find the method by name
    if not hasattr(notification, trigger_event):
        raise ValueError(f"Unknown trigger event: {trigger_event}")

    method = getattr(notification, trigger_event)

    try:
        res = method(**kwargs)  # each method decides what it needs
    except TypeError as e:
        # friendly error: show expected params for this method
        params = [p for p in signature(method).parameters.values() if p.name != "self"]
        expected = ", ".join(str(p) for p in params) or "(no params)"
        raise TypeError(f"{trigger_event} expected parameters: {expected}. Error: {e}")

    # send the email
    return email_client.send_email(
        to=to,
        subject=res["subject"],
        body=res["html"]
    )