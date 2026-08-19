from unittest import mock

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase, override_settings
from wagtail_2fa.middleware import VerifyUserPermissionsMiddleware

from climweb.base.middleware import SuperuserVerifyUserMiddleware


def _user(is_superuser=False, is_authenticated=True, is_staff=True):
    user = mock.Mock()
    user.is_superuser = is_superuser
    user.is_authenticated = is_authenticated
    user.is_staff = is_staff
    user.is_verified.return_value = False
    user.has_perms.return_value = is_superuser  # Django grants superusers everything
    return user


def _request(path="/cms-admin/", user=None, url_name="wagtailadmin_home"):
    request = RequestFactory().get(path)
    request.user = user if user is not None else _user(is_superuser=True)
    request._test_url_name = url_name
    return request


def _middleware():
    return SuperuserVerifyUserMiddleware(lambda request: None)


@override_settings(ADMIN_URL_PATH="cms-admin", DJANGO_ADMIN_URL_PATH="dj-ad-admin")
class RequireVerifiedUserTests(SimpleTestCase):
    """`WAGTAIL_2FA_REQUIRED=False` is what every existing .env actually says."""

    def setUp(self):
        self.mw = _middleware()
        patcher = mock.patch.object(
            SuperuserVerifyUserMiddleware,
            "_url_name",
            side_effect=lambda request: request._test_url_name,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    @override_settings(WAGTAIL_2FA_REQUIRED=False, CLIMWEB_2FA_SUPERUSER_REQUIRED=True)
    def test_superuser_is_required_even_when_the_flag_is_off(self):
        self.assertTrue(self.mw._require_verified_user(_request()))

    @override_settings(WAGTAIL_2FA_REQUIRED=False, CLIMWEB_2FA_SUPERUSER_REQUIRED=True)
    def test_plain_staff_user_is_untouched(self):
        """Non-superusers keep falling through to wagtail-2fa's own logic."""
        request = _request(user=_user(is_superuser=False))
        self.assertFalse(self.mw._require_verified_user(request))

    @override_settings(WAGTAIL_2FA_REQUIRED=False, CLIMWEB_2FA_SUPERUSER_REQUIRED=False)
    def test_escape_hatch_disables_the_superuser_rule(self):
        self.assertFalse(self.mw._require_verified_user(_request()))

    @override_settings(WAGTAIL_2FA_REQUIRED=False, CLIMWEB_2FA_SUPERUSER_REQUIRED=True)
    def test_anonymous_user_is_not_forced(self):
        request = _request(user=AnonymousUser())
        self.assertFalse(self.mw._require_verified_user(request))

    @override_settings(WAGTAIL_2FA_REQUIRED=False, CLIMWEB_2FA_SUPERUSER_REQUIRED=True)
    def test_login_and_auth_pages_are_exempt(self):
        """Otherwise the redirect below would bounce forever."""
        for url_name in SuperuserVerifyUserMiddleware._allowed_url_names:
            with self.subTest(url_name=url_name):
                request = _request(url_name=url_name)
                self.assertFalse(self.mw._require_verified_user(request))

    @override_settings(WAGTAIL_2FA_REQUIRED=False, CLIMWEB_2FA_SUPERUSER_REQUIRED=True)
    def test_enrolment_pages_are_exempt_while_the_user_has_no_device(self):
        for url_name in SuperuserVerifyUserMiddleware._allowed_url_names_no_device:
            with self.subTest(url_name=url_name):
                request = _request(url_name=url_name)
                with mock.patch(
                    "climweb.base.middleware.django_otp.user_has_device",
                    return_value=False,
                ):
                    self.assertFalse(self.mw._require_verified_user(request))

    @override_settings(WAGTAIL_2FA_REQUIRED=False, CLIMWEB_2FA_SUPERUSER_REQUIRED=True)
    def test_enrolment_pages_still_require_verification_once_enrolled(self):
        request = _request(url_name="wagtail_2fa_device_list")
        with mock.patch(
            "climweb.base.middleware.django_otp.user_has_device", return_value=True
        ):
            self.assertTrue(self.mw._require_verified_user(request))


@override_settings(
    ADMIN_URL_PATH="cms-admin",
    DJANGO_ADMIN_URL_PATH="dj-ad-admin",
    WAGTAIL_2FA_REQUIRED=False,
    CLIMWEB_2FA_SUPERUSER_REQUIRED=True,
)
class AdminPathScopingTests(SimpleTestCase):
    """The rule applies to the admins only, not the whole site."""

    def setUp(self):
        self.mw = _middleware()
        patcher = mock.patch.object(
            SuperuserVerifyUserMiddleware,
            "_url_name",
            side_effect=lambda request: request._test_url_name,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_wagtail_admin_is_covered(self):
        self.assertTrue(self.mw._superuser_forced(_request("/cms-admin/pages/")))

    def test_django_admin_is_covered(self):
        """It can edit users and delete other people's 2FA devices."""
        self.assertTrue(self.mw._superuser_forced(_request("/dj-ad-admin/auth/user/")))

    def test_public_site_is_not_covered(self):
        for path in ("/", "/news/", "/api/v2/pages/", "/cms-administrator-blog/"):
            with self.subTest(path=path):
                self.assertFalse(self.mw._superuser_forced(_request(path)))

    def test_public_page_leaves_verification_to_upstream(self):
        request = _request("/news/")
        self.assertFalse(self.mw._require_verified_user(request))

    def test_uses_path_info_so_force_script_name_still_matches(self):
        request = RequestFactory().get("/cms-admin/pages/", SCRIPT_NAME="/climweb")
        request.user = _user(is_superuser=True)
        request._test_url_name = "wagtailadmin_home"

        self.assertTrue(request.path.startswith("/climweb/"))
        self.assertTrue(self.mw._superuser_forced(request))

    @override_settings(ADMIN_URL_PATH="", DJANGO_ADMIN_URL_PATH="")
    def test_no_admin_paths_configured_means_nothing_is_forced(self):
        self.assertFalse(self.mw._superuser_forced(_request("/cms-admin/")))


@override_settings(ADMIN_URL_PATH="cms-admin", DJANGO_ADMIN_URL_PATH="dj-ad-admin")
class UrlResolutionTests(SimpleTestCase):
    @override_settings(WAGTAIL_2FA_REQUIRED=False, CLIMWEB_2FA_SUPERUSER_REQUIRED=True)
    def test_unresolvable_url_does_not_raise(self):
        """This middleware sees every request, including ones headed for a 404."""
        mw = _middleware()
        request = RequestFactory().get("/cms-admin/no-such-path-at-all/")
        request.user = _user(is_superuser=True)

        self.assertIsNone(mw._url_name(request))
        # Still enforced — an unknown URL is not an exemption.
        self.assertTrue(mw._require_verified_user(request))


@override_settings(ADMIN_URL_PATH="cms-admin", DJANGO_ADMIN_URL_PATH="dj-ad-admin")
class ProcessRequestTests(SimpleTestCase):
    """Only the branch this subclass adds; the parent is stubbed out."""

    def setUp(self):
        self.mw = _middleware()
        parent = mock.patch.object(
            VerifyUserPermissionsMiddleware, "process_request", return_value=None
        )
        parent.start()
        self.addCleanup(parent.stop)

        url_name = mock.patch.object(
            SuperuserVerifyUserMiddleware,
            "_url_name",
            side_effect=lambda request: request._test_url_name,
        )
        url_name.start()
        self.addCleanup(url_name.stop)

    @override_settings(WAGTAIL_2FA_REQUIRED=False, CLIMWEB_2FA_SUPERUSER_REQUIRED=True)
    def test_superuser_without_a_device_is_sent_to_enrolment(self):
        with mock.patch(
            "climweb.base.middleware.django_otp.user_has_device", return_value=False
        ):
            response = self.mw.process_request(_request())

        self.assertEqual(response.status_code, 302)
        self.assertIn("2fa/devices/new", response.url)

    @override_settings(WAGTAIL_2FA_REQUIRED=False, CLIMWEB_2FA_SUPERUSER_REQUIRED=True)
    def test_enrolled_superuser_is_left_to_the_parent(self):
        """The parent already issues the "verify your code" redirect."""
        with mock.patch(
            "climweb.base.middleware.django_otp.user_has_device", return_value=True
        ):
            self.assertIsNone(self.mw.process_request(_request()))

    @override_settings(WAGTAIL_2FA_REQUIRED=False, CLIMWEB_2FA_SUPERUSER_REQUIRED=True)
    def test_non_superuser_gets_no_extra_redirect(self):
        request = _request(user=_user(is_superuser=False))
        with mock.patch(
            "climweb.base.middleware.django_otp.user_has_device", return_value=False
        ):
            self.assertIsNone(self.mw.process_request(request))

    @override_settings(WAGTAIL_2FA_REQUIRED=False, CLIMWEB_2FA_SUPERUSER_REQUIRED=False)
    def test_escape_hatch_short_circuits_the_redirect(self):
        with mock.patch(
            "climweb.base.middleware.django_otp.user_has_device", return_value=False
        ):
            self.assertIsNone(self.mw.process_request(_request()))

    @override_settings(WAGTAIL_2FA_REQUIRED=False, CLIMWEB_2FA_SUPERUSER_REQUIRED=True)
    def test_a_parent_response_is_never_overridden(self):
        sentinel = mock.Mock(status_code=302)
        with mock.patch.object(
            VerifyUserPermissionsMiddleware, "process_request", return_value=sentinel
        ):
            self.assertIs(self.mw.process_request(_request()), sentinel)
