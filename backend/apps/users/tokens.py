from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """Same HMAC scheme as Django's password reset tokens, with a distinct salt
    so a verification token can never be replayed as a password reset token."""

    key_salt = "apps.users.tokens.EmailVerificationTokenGenerator"

    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{user.email}{user.is_verified}{timestamp}"


email_verification_token_generator = EmailVerificationTokenGenerator()
