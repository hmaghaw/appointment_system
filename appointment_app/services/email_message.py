class EmailMessage():
    def __init__(self, business_name="YourApp", support_url="https://example.com/support"):
        self.business_name = business_name
        self.support_url = support_url
        self.dashboard_url = "halalcooking.ca"
        self.our_business_name = "Voxxel"

    def _wrap(self, body_html):
        return (
            f'<div style="font-family:Arial, sans-serif;max-width:640px;margin:auto;padding:16px">'
            f'{body_html}'
            f'<hr style="border:none;border-top:1px solid #eee;margin-top:24px">'
            f'<p style="font-size:12px;color:#888">© {self.business_name} · '
            f'<a href="{self.support_url}">Support</a></p></div>'
        )

    # ---- events (each builds its body inside) ------------------------------
    def user_signed_up(self, first_name, business_name):
        subject = f"Welcome {first_name} and {business_name} to {self.our_business_name}!"
        html = self._wrap(
            f"<h1>Welcome to {self.our_business_name} 🎉</h1>"
            f"<p>Hi {first_name}, we’re excited to have you and your business "
            f"<strong>{business_name}</strong> join our community.</p>"
            f"<p>With {self.our_business_name}, you can manage your business more efficiently, "
            f"connect with customers, and unlock powerful tools designed for growth.</p>"
            f'<p>Get started here: <a href="{self.dashboard_url}">{self.dashboard_url}</a></p>'
        )
        text = (
            f"Hi {first_name}, welcome to {self.our_business_name}! "
            f"We’re excited to have you and {business_name} join us.\n"
            f"Start here: {self.dashboard_url}"
        )
        return {
            "subject": subject,
            "html": html,
            "text": text,
        }

    def email_verification(self, first_name, verify_url, expires_minutes=60):
        subject = f"Verify your email for {self.our_business_name}"
        html = self._wrap(
            f"<h1>Verify your email</h1>"
            f"<p>Hi {first_name}, please confirm your email to finish setting up your account.</p>"
            f"<p>This link expires in {expires_minutes} minutes.</p>"
            f'<p><a href="{verify_url}">{verify_url}</a></p>'
            f'<p>After verification, you can access your dashboard here: '
            f'<a href="{self.dashboard_url}">{self.dashboard_url}</a></p>'
        )
        text = (
            f"Hi {first_name}, confirm your email for {self.our_business_name}.\n"
            f"Link (expires in {expires_minutes} minutes): {verify_url}\n"
            f"Dashboard: {self.dashboard_url}"
        )
        result = {
            "subject": subject,
            "html": html,
            "text": text,
        }
        return result

    def password_reset_request(self, first_name, reset_url, ttl_minutes=60):
        subject = f"Reset your {self.our_business_name} password"
        html = self._wrap(
            f"<h1>Password reset</h1>"
            f"<p>Hi {first_name}, click the link below to reset your password.</p>"
            f"<p>This link expires in {ttl_minutes} minutes.</p>"
            f'<p><a href="{reset_url}">{reset_url}</a></p>'
        )
        text = (
            f"Hi {first_name}, reset your {self.our_business_name} password.\n"
            f"Link (expires in {ttl_minutes} minutes): {reset_url}"
        )
        result = {
            "subject": subject,
            "html": html,
            "text": text,
        }
        return result

    def password_changed(self, first_name):
        subject = f"Your {self.our_business_name} password was changed"
        html = self._wrap(
            f"<h1>Password changed</h1>"
            f"<p>Hi {first_name}, your password was just changed.</p>"
            f"<p>If you did not make this change, please reset your password immediately.</p>"
            f'<p>Go to your dashboard: <a href="{self.dashboard_url}">{self.dashboard_url}</a></p>'
        )
        text = (
            f"Hi {first_name}, your {self.our_business_name} password was changed.\n"
            f"If this wasn’t you, reset it immediately.\n"
            f"Dashboard: {self.dashboard_url}"
        )
        result = {
            "subject": subject,
            "html": html,
            "text": text,
        }
        return result
