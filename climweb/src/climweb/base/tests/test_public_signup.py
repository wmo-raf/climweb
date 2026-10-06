from django.contrib.auth import get_user_model
from django.test import TestCase


class PublicSignupClosedTests(TestCase):
    def test_signup_page_says_signup_is_closed(self):
        response = self.client.get("/auth/signup/")
        self.assertTemplateUsed(response, "account/signup_closed.html")

    def test_posting_the_signup_form_creates_no_account(self):
        self.client.post(
            "/auth/signup/",
            {
                "username": "spammer",
                "email": "spam@example.com",
                "password1": "a-Long-pass-123",
                "password2": "a-Long-pass-123",
            },
        )
        self.assertFalse(get_user_model().objects.filter(username="spammer").exists())

    def test_password_reset_still_works(self):
        """geomanager emails users allauth password-reset links under /auth/."""
        self.assertEqual(self.client.get("/auth/password/reset/").status_code, 200)
