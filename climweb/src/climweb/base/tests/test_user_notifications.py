from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings

User = get_user_model()


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="climweb@example.com",
    WAGTAIL_SITE_NAME="Test Met",
    WAGTAILADMIN_BASE_URL="https://met.example",
)
class NewUserNotificationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@met.example", password="x"
        )
        mail.outbox.clear()

    def _create(self, **kwargs):
        kwargs.setdefault("username", "newbie")
        kwargs.setdefault("email", "newbie@met.example")
        with self.captureOnCommitCallbacks(execute=True):
            return User.objects.create_user(password="x", **kwargs)

    def test_superusers_are_emailed_about_a_new_user(self):
        user = self._create(first_name="New", last_name="Bie")

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ["admin@met.example"])
        self.assertEqual(message.subject, "New user account on Test Met: newbie")
        self.assertIn("New Bie", message.body)
        self.assertIn("newbie@met.example", message.body)
        self.assertIn(f"https://met.example/cms-admin/users/edit/{user.pk}/", message.body)

    def test_a_new_superuser_is_called_out(self):
        with self.captureOnCommitCallbacks(execute=True):
            User.objects.create_superuser(username="boss", email="b@met.example", password="x")

        self.assertEqual(mail.outbox[0].subject, "New superuser account on Test Met: boss")
        self.assertIn("Superuser (full access to everything)", mail.outbox[0].body)

    def test_every_active_superuser_with_an_email_is_notified(self):
        User.objects.create_superuser(username="admin2", email="admin2@met.example", password="x")
        User.objects.create_superuser(username="noemail", email="", password="x")
        User.objects.create_superuser(
            username="gone", email="gone@met.example", password="x", is_active=False
        )
        User.objects.create_user(username="editor", email="editor@met.example", password="x")

        self._create()

        self.assertCountEqual(
            mail.outbox[0].to, ["admin@met.example", "admin2@met.example"]
        )

    def test_the_new_superuser_is_not_told_about_themselves(self):
        with self.captureOnCommitCallbacks(execute=True):
            User.objects.create_superuser(username="boss", email="b@met.example", password="x")

        self.assertEqual(mail.outbox[0].to, ["admin@met.example"])

    def test_editing_an_existing_user_sends_nothing(self):
        user = self._create()
        mail.outbox.clear()

        with self.captureOnCommitCallbacks(execute=True):
            user.first_name = "Changed"
            user.save()

        self.assertEqual(len(mail.outbox), 0)

    def test_nothing_is_sent_if_the_creation_is_rolled_back(self):
        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            User.objects.create_user(username="newbie", password="x")
        # The transaction never commits, so the callback never runs.
        self.assertEqual(len(callbacks), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_first_superuser_with_nobody_to_tell_is_fine(self):
        self.admin.delete()
        with self.captureOnCommitCallbacks(execute=True):
            User.objects.create_superuser(username="first", email="f@met.example", password="x")
        self.assertEqual(len(mail.outbox), 0)

    def test_mail_failure_does_not_break_user_creation(self):
        with mock.patch(
            "climweb.base.user_notifications.send_mail", side_effect=OSError("smtp down")
        ):
            user = self._create()
        self.assertTrue(User.objects.filter(pk=user.pk).exists())

    @override_settings(WAGTAILADMIN_BASE_URL="")
    def test_link_falls_back_to_a_path_without_a_base_url(self):
        user = self._create()
        self.assertIn(f"\n/cms-admin/users/edit/{user.pk}/\n", mail.outbox[0].body)
