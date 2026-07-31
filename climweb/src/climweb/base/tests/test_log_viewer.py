from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from climweb.base.logs import docker_client

PROXY = "tcp://climweb_docker_proxy:2375"


class _FakeContainer:
    """Stands in for a docker-py Container, with one deliberate landmine.

    Touching `.image` raises, because that property issues a second request to
    /images/{id}/json which the socket proxy blocks (IMAGES is off) — it 403s
    the whole container listing. Anything that reaches for it should fail loudly
    in the tests rather than in production.
    """

    def __init__(self, name, status="running", image_ref="climweb:local"):
        self.name = name
        self.status = status
        self.attrs = {
            "Name": f"/{name}",
            "State": {"Status": status},
            "Config": {"Image": image_ref},
            "Image": "sha256:6cbdd4bfb4ec6156e34251b1b3f5739cc1a4b5003",
        }
        self.logs = mock.Mock(return_value=b"")

    @property
    def image(self):
        raise AssertionError(
            "container.image triggers a blocked /images/{id}/json request"
        )


def _fake_container(name, status="running", image_ref="climweb:local"):
    return _FakeContainer(name, status=status, image_ref=image_ref)


def _client_with(containers):
    client = mock.Mock()
    client.containers.list.return_value = containers
    return client


class RedactionTests(SimpleTestCase):
    def test_redacts_secret_looking_env_values(self):
        env = {
            "SECRET_KEY": "sup3r-s3cret-django-key",
            "CMS_DB_PASSWORD": "hunter2hunter2",
            "TIME_ZONE": "Africa/Nairobi",
        }
        with mock.patch.dict(docker_client.os.environ, env, clear=True):
            out = docker_client.redact(
                "boot in Africa/Nairobi with key sup3r-s3cret-django-key "
                "and pw hunter2hunter2"
            )

        self.assertNotIn("sup3r-s3cret-django-key", out)
        self.assertNotIn("hunter2hunter2", out)
        self.assertEqual(out.count("[redacted]"), 2)
        # Non-sensitive values must survive, or the logs become useless.
        self.assertIn("Africa/Nairobi", out)

    def test_redacts_password_inside_connection_string(self):
        env = {
            "DATABASE_URL":
                "postgis://climweb:tops3cretpw@climweb_pgbouncer:5432/climweb"
        }
        with mock.patch.dict(docker_client.os.environ, env, clear=True):
            out = docker_client.redact("OperationalError connecting as tops3cretpw")

        self.assertNotIn("tops3cretpw", out)

    def test_short_values_are_not_redacted(self):
        """Masking short values would shred unrelated log text."""
        with mock.patch.dict(docker_client.os.environ, {"API_KEY": "abc"}, clear=True):
            self.assertEqual(docker_client.redact("abc def"), "abc def")

    @override_settings(CLIMWEB_LOG_VIEWER_EXTRA_REDACTIONS=["custom-tenant-token"])
    def test_extra_redactions_from_settings(self):
        with mock.patch.dict(docker_client.os.environ, {}, clear=True):
            out = docker_client.redact("t=custom-tenant-token")
        self.assertNotIn("custom-tenant-token", out)


class LineParsingTests(SimpleTestCase):
    def test_parse_rfc3339_handles_docker_precision(self):
        for value in (
            "2026-07-31T09:15:10.500000000Z",   # docker's nanosecond precision
            "2026-07-31T09:15:10.500000Z",
            "2026-07-31T09:15:10Z",
        ):
            with self.subTest(value=value):
                parsed = docker_client._parse_rfc3339(value)
                self.assertEqual(
                    (parsed.year, parsed.hour, parsed.second), (2026, 9, 10)
                )

    def test_parse_line_levels(self):
        cases = [
            ("2026-07-31T09:15:00.123456789Z ERROR 2026-07-31 boom", "ERROR"),
            ("2026-07-31T09:15:00.123456789Z WARN something odd", "WARNING"),
            ("2026-07-31T09:15:00.123456789Z FATAL gone", "CRITICAL"),
            ('2026-07-31T09:15:00.123456789Z   File "x.py", line 1', ""),
        ]
        for raw, level in cases:
            with self.subTest(raw=raw):
                parsed = docker_client._parse_line(raw)
                self.assertEqual(parsed["level"], level)
                self.assertEqual(parsed["ts"], "2026-07-31T09:15:00.123456789Z")

    def test_parse_line_without_timestamp(self):
        parsed = docker_client._parse_line("plain line")
        self.assertEqual(parsed["ts"], "")
        self.assertEqual(parsed["message"], "plain line")

    def test_parse_line_skips_blank(self):
        self.assertIsNone(docker_client._parse_line(""))

    def test_timestamps_sort_lexicographically(self):
        """The view dedupes with a string `>` comparison, so this must hold."""
        earlier = "2026-07-31T09:15:00.100000000Z"
        later = "2026-07-31T09:15:00.200000000Z"
        self.assertGreater(later, earlier)
        self.assertGreater("2026-07-31T10:00:00.000000000Z", later)


class AllowListTests(SimpleTestCase):
    def setUp(self):
        cache.delete(docker_client.CACHE_KEY_CONTAINERS)
        self.addCleanup(cache.delete, docker_client.CACHE_KEY_CONTAINERS)

    @override_settings(
        CLIMWEB_LOG_VIEWER_ENABLED=True,
        CLIMWEB_DOCKER_HOST=PROXY,
        CLIMWEB_LOG_VIEWER_CONTAINERS=[],
        CLIMWEB_LOG_VIEWER_NAME_PREFIX="climweb",
    )
    def test_prefix_filters_out_unrelated_containers(self):
        client = _client_with([
            _fake_container("climweb"),
            _fake_container("climweb_celery_worker"),
            _fake_container("someone_elses_app"),
        ])
        with mock.patch.object(docker_client, "get_client", return_value=client):
            names = [c["name"] for c in docker_client.list_containers(use_cache=False)]

        self.assertNotIn("someone_elses_app", names)
        self.assertEqual(names[0], "climweb", "the CMS container should sort first")
        self.assertIn("climweb_celery_worker", names)

    @override_settings(
        CLIMWEB_LOG_VIEWER_ENABLED=True,
        CLIMWEB_DOCKER_HOST=PROXY,
        CLIMWEB_LOG_VIEWER_CONTAINERS=["climweb"],
    )
    def test_explicit_allow_list_wins_over_prefix(self):
        client = _client_with([
            _fake_container("climweb"),
            _fake_container("climweb_db"),
        ])
        with mock.patch.object(docker_client, "get_client", return_value=client):
            names = [c["name"] for c in docker_client.list_containers(use_cache=False)]

        self.assertEqual(names, ["climweb"])

    @override_settings(
        CLIMWEB_LOG_VIEWER_ENABLED=True,
        CLIMWEB_DOCKER_HOST=PROXY,
        CLIMWEB_LOG_VIEWER_CONTAINERS=["climweb"],
    )
    def test_image_is_read_from_attrs_not_the_images_endpoint(self):
        """Regression: `container.image` 403s against the socket proxy."""
        client = _client_with([_fake_container("climweb", image_ref="climweb:local")])
        with mock.patch.object(docker_client, "get_client", return_value=client):
            listed = docker_client.list_containers(use_cache=False)

        self.assertEqual(listed[0]["image"], "climweb:local")

    @override_settings(
        CLIMWEB_LOG_VIEWER_ENABLED=True,
        CLIMWEB_DOCKER_HOST=PROXY,
        CLIMWEB_LOG_VIEWER_CONTAINERS=["climweb"],
    )
    def test_image_falls_back_to_digest_when_config_is_absent(self):
        """The sparse list payload has no Config, only a top-level Image."""
        container = _fake_container("climweb")
        container.attrs.pop("Config")
        client = _client_with([container])
        with mock.patch.object(docker_client, "get_client", return_value=client):
            listed = docker_client.list_containers(use_cache=False)

        self.assertTrue(listed[0]["image"].startswith("sha256:"))

    @override_settings(
        CLIMWEB_LOG_VIEWER_ENABLED=True,
        CLIMWEB_DOCKER_HOST=PROXY,
        CLIMWEB_LOG_VIEWER_CONTAINERS=["climweb"],
    )
    def test_disallowed_container_is_rejected_before_any_docker_call(self):
        client = _client_with([_fake_container("climweb")])
        with mock.patch.object(docker_client, "get_client", return_value=client):
            with self.assertRaises(docker_client.LogViewerError):
                docker_client.resolve_container("some_other_container")

        client.containers.get.assert_not_called()

    @override_settings(CLIMWEB_LOG_VIEWER_ENABLED=False)
    def test_disabled_instance_refuses_to_build_a_client(self):
        with self.assertRaises(docker_client.LogViewerDisabled):
            docker_client.get_client()

    @override_settings(CLIMWEB_LOG_VIEWER_ENABLED=True, CLIMWEB_DOCKER_HOST="")
    def test_missing_docker_host_is_treated_as_disabled(self):
        with self.assertRaises(docker_client.LogViewerDisabled):
            docker_client.get_client()


class EnabledGateTests(SimpleTestCase):
    """The flag defaults on, so a configured proxy is what actually decides."""

    @override_settings(CLIMWEB_LOG_VIEWER_ENABLED=True, CLIMWEB_DOCKER_HOST=PROXY)
    def test_on_when_flag_set_and_proxy_configured(self):
        self.assertTrue(docker_client.is_enabled())

    @override_settings(CLIMWEB_LOG_VIEWER_ENABLED=True, CLIMWEB_DOCKER_HOST="")
    def test_off_without_a_proxy_even_though_the_flag_defaults_on(self):
        """An instance on an older compose file must not advertise the feature."""
        self.assertFalse(docker_client.is_enabled())

    @override_settings(CLIMWEB_LOG_VIEWER_ENABLED=False, CLIMWEB_DOCKER_HOST=PROXY)
    def test_explicit_opt_out_wins_over_a_running_proxy(self):
        self.assertFalse(docker_client.is_enabled())


@override_settings(
    CLIMWEB_LOG_VIEWER_ENABLED=True,
    CLIMWEB_DOCKER_HOST=PROXY,
    CLIMWEB_LOG_VIEWER_CONTAINERS=["climweb"],
)
class FetchTests(SimpleTestCase):
    def setUp(self):
        cache.delete(docker_client.CACHE_KEY_CONTAINERS)
        self.addCleanup(cache.delete, docker_client.CACHE_KEY_CONTAINERS)

        self.container = _fake_container("climweb")
        self.container.logs.return_value = b""
        self.client_mock = _client_with([self.container])
        self.client_mock.containers.get.return_value = self.container

        patcher = mock.patch.object(
            docker_client, "get_client", return_value=self.client_mock
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_fetch_logs_parses_and_redacts(self):
        self.container.logs.return_value = (
            b"2026-07-31T09:15:00.000000001Z INFO started\n"
            b"2026-07-31T09:15:01.000000001Z ERROR bad key leaked-secret-value\n"
        )
        env = {"SECRET_KEY": "leaked-secret-value"}
        with mock.patch.dict(docker_client.os.environ, env, clear=True):
            lines = docker_client.fetch_logs("climweb", tail=10)

        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0]["level"], "INFO")
        self.assertEqual(lines[1]["level"], "ERROR")
        self.assertNotIn("leaked-secret-value", lines[1]["message"])
        self.assertTrue(self.container.logs.call_args.kwargs["timestamps"])

    def test_tail_is_clamped_to_max_lines(self):
        docker_client.fetch_logs("climweb", tail=10_000_000, max_lines=500)
        self.assertEqual(self.container.logs.call_args.kwargs["tail"], 500)

    def test_since_is_passed_as_a_datetime_one_second_early(self):
        """Docker's `since` has one-second granularity; over-fetch and dedupe."""
        docker_client.fetch_logs("climweb", since="2026-07-31T09:15:10.500000000Z")

        since = self.container.logs.call_args.kwargs["since"]
        self.assertEqual(since.year, 2026)
        self.assertEqual(since.second, 9)

    def test_unparseable_since_falls_back_to_tail(self):
        docker_client.fetch_logs("climweb", tail=42, since="not-a-timestamp")

        self.assertNotIn("since", self.container.logs.call_args.kwargs)
        self.assertEqual(self.container.logs.call_args.kwargs["tail"], 42)

    def test_docker_errors_become_friendly_messages(self):
        self.container.logs.side_effect = RuntimeError("connection refused")
        with self.assertRaisesMessage(
            docker_client.LogViewerError, "connection refused"
        ):
            docker_client.fetch_logs("climweb")


class LogViewPermissionTests(TestCase):
    def setUp(self):
        cache.delete(docker_client.CACHE_KEY_CONTAINERS)
        self.addCleanup(cache.delete, docker_client.CACHE_KEY_CONTAINERS)

    def test_non_superuser_cannot_reach_the_log_endpoints(self):
        editor = get_user_model().objects.create_user(
            username="editor", password="pw12345!", is_staff=True
        )
        self.client.force_login(editor)

        for name in ("log-viewer", "log-fetch", "log-download"):
            with self.subTest(url=name):
                response = self.client.get(reverse(name), {"container": "climweb"})
                self.assertEqual(response.status_code, 403)

    @override_settings(
        CLIMWEB_LOG_VIEWER_ENABLED=True,
        CLIMWEB_DOCKER_HOST=PROXY,
        CLIMWEB_LOG_VIEWER_CONTAINERS=["climweb"],
    )
    def test_fetch_drops_lines_the_client_already_has(self):
        admin = get_user_model().objects.create_superuser(
            username="admin", password="pw12345!", email="a@example.com"
        )
        self.client.force_login(admin)

        returned = [
            {"ts": "2026-07-31T09:15:00.000000001Z", "level": "INFO", "message": "old"},
            {"ts": "2026-07-31T09:15:09.000000001Z", "level": "INFO", "message": "new"},
        ]
        with mock.patch(
            "climweb.base.logs.views.fetch_logs", return_value=returned
        ):
            response = self.client.get(
                reverse("log-fetch"),
                {"container": "climweb", "since": "2026-07-31T09:15:05.000000000Z"},
            )

        payload = response.json()
        self.assertEqual([line["message"] for line in payload["lines"]], ["new"])
        self.assertEqual(payload["latest"], "2026-07-31T09:15:09.000000001Z")
