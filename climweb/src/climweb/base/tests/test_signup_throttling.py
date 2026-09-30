from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from climweb.base.signup_throttling import client_ip

RATES = {
    "register_per_ip": "2/hour",
    "register_site_wide": "3/day",
    "password_reset_per_ip": "2/hour",
    "password_reset_site_wide": "3/day",
}


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
    PUBLIC_ACCOUNT_RATE_LIMITS=RATES,
    AXES_IPWARE_PROXY_COUNT=1,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="climweb@example.com",
)
class PublicAccountThrottleTests(TestCase):
    def setUp(self):
        cache.clear()

    def _register(self, email, ip="203.0.113.1"):
        return self.client.post(
            "/api/auth/register/",
            {"username": email},
            content_type="application/json",
            HTTP_X_FORWARDED_FOR=ip,
        )

    def _reset(self, email, ip="203.0.113.1"):
        return self.client.post(
            "/api/auth/reset-password/",
            {"username": email},
            content_type="application/json",
            HTTP_X_FORWARDED_FOR=ip,
        )

    def test_registration_still_works(self):
        response = self._register("viewer@example.com")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(get_user_model().objects.filter(email="viewer@example.com").exists())

    def test_one_ip_is_limited(self):
        self.assertEqual(self._register("a@example.com").status_code, 201)
        self.assertEqual(self._register("b@example.com").status_code, 201)

        response = self._register("c@example.com")

        self.assertEqual(response.status_code, 429)
        self.assertIn("Retry-After", response)
        self.assertFalse(get_user_model().objects.filter(email="c@example.com").exists())

    def test_another_ip_is_not_affected_by_the_first(self):
        self._register("a@example.com")
        self._register("b@example.com")
        self.assertEqual(self._register("c@example.com", ip="198.51.100.7").status_code, 201)

    def test_the_whole_site_is_capped_across_many_ips(self):
        for n in range(3):
            self.assertEqual(self._register(f"u{n}@example.com", ip=f"198.51.100.{n}").status_code, 201)
        self.assertEqual(self._register("u9@example.com", ip="198.51.100.9").status_code, 429)

    def test_forging_x_forwarded_for_does_not_reset_the_limit(self):
        """nginx appends the real address; the bot can only add to the left."""
        self._register("a@example.com", ip="1.1.1.1, 203.0.113.1")
        self._register("b@example.com", ip="2.2.2.2, 203.0.113.1")
        self.assertEqual(self._register("c@example.com", ip="3.3.3.3, 203.0.113.1").status_code, 429)

    def test_password_reset_is_limited_separately(self):
        get_user_model().objects.create_user(username="v", email="v@example.com", password="x")
        self._register("a@example.com")
        self._register("b@example.com")

        self.assertEqual(self._reset("v@example.com").status_code, 201)
        self.assertEqual(self._reset("v@example.com").status_code, 201)
        self.assertEqual(self._reset("v@example.com").status_code, 429)


class ClientIPTests(SimpleTestCase):
    def _ip(self, xff=None, remote="10.0.0.2"):
        meta = {"REMOTE_ADDR": remote}
        if xff is not None:
            meta["HTTP_X_FORWARDED_FOR"] = xff
        return client_ip(RequestFactory().get("/", **meta))

    @override_settings(AXES_IPWARE_PROXY_COUNT=2)
    def test_two_proxies_take_the_second_from_the_right(self):
        # client -> outer proxy (adds client) -> nginx (adds outer proxy) -> Django
        self.assertEqual(self._ip("forged, 203.0.113.1, 10.0.0.1"), "203.0.113.1")

    @override_settings(AXES_IPWARE_PROXY_COUNT=1)
    def test_one_proxy_takes_the_rightmost(self):
        self.assertEqual(self._ip("forged, 203.0.113.1"), "203.0.113.1")

    @override_settings(AXES_IPWARE_PROXY_COUNT=0)
    def test_no_proxies_ignores_the_header(self):
        self.assertEqual(self._ip("forged", remote="203.0.113.1"), "203.0.113.1")

    @override_settings(AXES_IPWARE_PROXY_COUNT=1)
    def test_no_header_falls_back_to_the_connection(self):
        self.assertEqual(self._ip(remote="203.0.113.1"), "203.0.113.1")
