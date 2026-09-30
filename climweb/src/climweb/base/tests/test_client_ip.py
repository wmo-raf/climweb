from axes.helpers import get_client_ip_address
from axes.models import AccessAttempt
from django.contrib.auth import authenticate, get_user_model
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

CLIENT = "203.0.113.7"
FORGED = "198.51.100.66"
OTHER_CLIENT = "203.0.113.99"
OUTER_PROXY = "192.0.2.10"
NGINX = "172.18.0.5"


def _request(xff=None, remote_addr=NGINX):
    meta = {"REMOTE_ADDR": remote_addr}
    if xff is not None:
        meta["HTTP_X_FORWARDED_FOR"] = xff
    return RequestFactory().post("/admin/login/", **meta)


class AxesClientIPTests(SimpleTestCase):
    @override_settings(AXES_IPWARE_PROXY_COUNT=1)
    def test_one_proxy(self):
        # client -> nginx -> django
        self.assertEqual(get_client_ip_address(_request(CLIENT)), CLIENT)

    @override_settings(AXES_IPWARE_PROXY_COUNT=1)
    def test_one_proxy_ignores_forged_entries(self):
        # The client sent its own X-Forwarded-For; nginx appended the real address.
        request = _request(f"{FORGED}, 10.0.0.1, {CLIENT}")
        self.assertEqual(get_client_ip_address(request), CLIENT)

    @override_settings(AXES_IPWARE_PROXY_COUNT=2)
    def test_two_proxies(self):
        # client -> outer proxy -> nginx -> django
        request = _request(f"{CLIENT}, {OUTER_PROXY}")
        self.assertEqual(get_client_ip_address(request), CLIENT)

    @override_settings(AXES_IPWARE_PROXY_COUNT=2)
    def test_two_proxies_ignores_forged_entries(self):
        request = _request(f"{FORGED}, {CLIENT}, {OUTER_PROXY}")
        self.assertEqual(get_client_ip_address(request), CLIENT)

    @override_settings(AXES_IPWARE_PROXY_COUNT=2)
    def test_two_proxies_short_chain_uses_leftmost(self):
        # The outer proxy was skipped, so only nginx appended.
        self.assertEqual(get_client_ip_address(_request(CLIENT)), CLIENT)

    @override_settings(AXES_IPWARE_PROXY_COUNT=2)
    def test_no_forwarded_header_falls_back_to_remote_addr(self):
        request = _request(remote_addr=CLIENT)
        self.assertEqual(get_client_ip_address(request), CLIENT)

    @override_settings(AXES_IPWARE_PROXY_COUNT=0)
    def test_no_proxies_uses_remote_addr_and_ignores_header(self):
        request = _request(FORGED, remote_addr=CLIENT)
        self.assertEqual(get_client_ip_address(request), CLIENT)

    @override_settings(AXES_IPWARE_PROXY_COUNT=2)
    def test_unparseable_entry_gives_none(self):
        # Must never reach AccessAttempt.ip_address (a GenericIPAddressField).
        request = _request(f"not-an-ip, {OUTER_PROXY}")
        self.assertIsNone(get_client_ip_address(request))


@override_settings(AXES_IPWARE_PROXY_COUNT=2, AXES_FAILURE_LIMIT=3)
class AxesLockoutByIPTests(TestCase):
    def setUp(self):
        get_user_model().objects.create_user(
            username="editor", email="editor@example.com", password="right-password"
        )

    def _login(self, xff, password="wrong"):
        request = _request(xff)
        request.META["HTTP_USER_AGENT"] = "test-agent"
        return authenticate(request=request, username="editor", password=password)

    def test_lockout_is_keyed_on_real_client_ip(self):
        attacker_chain = f"{CLIENT}, {OUTER_PROXY}"
        for _ in range(3):
            self._login(attacker_chain)

        attempt = AccessAttempt.objects.get(username="editor")
        self.assertEqual(attempt.ip_address, CLIENT)
        self.assertEqual(attempt.failures_since_start, 3)

        # The attacker stays locked out, even when forging a different address...
        self.assertIsNone(
            self._login(f"{FORGED}, {attacker_chain}", password="right-password")
        )
        # ...while the real user on another address can still sign in.
        self.assertIsNotNone(
            self._login(f"{OTHER_CLIENT}, {OUTER_PROXY}", password="right-password")
        )
