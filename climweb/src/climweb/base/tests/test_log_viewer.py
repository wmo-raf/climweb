from unittest import mock

import pytest
from django.test import override_settings

from climweb.base.logs import docker_client


@pytest.fixture(autouse=True)
def clear_container_cache():
    from django.core.cache import cache

    cache.delete(docker_client.CACHE_KEY_CONTAINERS)
    yield
    cache.delete(docker_client.CACHE_KEY_CONTAINERS)


def _fake_container(name, status="running", image_tag="ghcr.io/wmo-raf/climweb:v1"):
    container = mock.Mock()
    container.name = name
    container.status = status
    container.image.tags = [image_tag]
    return container


def _client_with(containers):
    client = mock.Mock()
    client.containers.list.return_value = containers
    return client


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------

def test_redacts_secret_looking_env_values():
    env = {
        "SECRET_KEY": "sup3r-s3cret-django-key",
        "CMS_DB_PASSWORD": "hunter2hunter2",
        "TIME_ZONE": "Africa/Nairobi",
    }
    with mock.patch.dict(docker_client.os.environ, env, clear=True):
        out = docker_client.redact(
            "boot in Africa/Nairobi with key sup3r-s3cret-django-key and pw hunter2hunter2"
        )

    assert "sup3r-s3cret-django-key" not in out
    assert "hunter2hunter2" not in out
    assert out.count("[redacted]") == 2
    # Non-sensitive values must survive, or the logs become useless.
    assert "Africa/Nairobi" in out


def test_redacts_password_inside_connection_string():
    env = {"DATABASE_URL": "postgis://climweb:tops3cretpw@climweb_pgbouncer:5432/climweb"}
    with mock.patch.dict(docker_client.os.environ, env, clear=True):
        out = docker_client.redact("OperationalError connecting as tops3cretpw")

    assert "tops3cretpw" not in out


def test_short_values_are_not_redacted():
    """Masking short values would shred unrelated log text."""
    with mock.patch.dict(docker_client.os.environ, {"API_KEY": "abc"}, clear=True):
        assert docker_client.redact("abc def") == "abc def"


@override_settings(CLIMWEB_LOG_VIEWER_EXTRA_REDACTIONS=["custom-tenant-token"])
def test_extra_redactions_from_settings():
    with mock.patch.dict(docker_client.os.environ, {}, clear=True):
        assert "custom-tenant-token" not in docker_client.redact("t=custom-tenant-token")


# ---------------------------------------------------------------------------
# Line parsing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "value",
    [
        "2026-07-31T09:15:10.500000000Z",   # docker's nanosecond precision
        "2026-07-31T09:15:10.500000Z",
        "2026-07-31T09:15:10Z",
    ],
)
def test_parse_rfc3339_handles_docker_precision(value):
    parsed = docker_client._parse_rfc3339(value)
    assert (parsed.year, parsed.hour, parsed.second) == (2026, 9, 10)


@pytest.mark.parametrize(
    "raw,level",
    [
        ("2026-07-31T09:15:00.123456789Z ERROR 2026-07-31 boom", "ERROR"),
        ("2026-07-31T09:15:00.123456789Z WARN something odd", "WARNING"),
        ("2026-07-31T09:15:00.123456789Z FATAL gone", "CRITICAL"),
        ("2026-07-31T09:15:00.123456789Z   File \"x.py\", line 1", ""),
    ],
)
def test_parse_line_levels(raw, level):
    parsed = docker_client._parse_line(raw)
    assert parsed["level"] == level
    assert parsed["ts"] == "2026-07-31T09:15:00.123456789Z"


def test_parse_line_without_timestamp():
    parsed = docker_client._parse_line("plain line")
    assert parsed["ts"] == ""
    assert parsed["message"] == "plain line"


def test_parse_line_skips_blank():
    assert docker_client._parse_line("") is None


def test_timestamps_sort_lexicographically():
    """The view dedupes with a string `>` comparison, so this must hold."""
    earlier = "2026-07-31T09:15:00.100000000Z"
    later = "2026-07-31T09:15:00.200000000Z"
    assert later > earlier
    assert "2026-07-31T10:00:00.000000000Z" > later


# ---------------------------------------------------------------------------
# Allow-list
# ---------------------------------------------------------------------------

@override_settings(
    CLIMWEB_LOG_VIEWER_ENABLED=True,
    CLIMWEB_DOCKER_HOST="tcp://climweb_docker_proxy:2375",
    CLIMWEB_LOG_VIEWER_CONTAINERS=[],
    CLIMWEB_LOG_VIEWER_NAME_PREFIX="climweb",
)
def test_prefix_filters_out_unrelated_containers():
    client = _client_with([
        _fake_container("climweb"),
        _fake_container("climweb_celery_worker"),
        _fake_container("someone_elses_app"),
    ])
    with mock.patch.object(docker_client, "get_client", return_value=client):
        names = [c["name"] for c in docker_client.list_containers(use_cache=False)]

    assert "someone_elses_app" not in names
    assert names[0] == "climweb", "the CMS container should sort first"
    assert "climweb_celery_worker" in names


@override_settings(
    CLIMWEB_LOG_VIEWER_ENABLED=True,
    CLIMWEB_DOCKER_HOST="tcp://climweb_docker_proxy:2375",
    CLIMWEB_LOG_VIEWER_CONTAINERS=["climweb"],
)
def test_explicit_allow_list_wins_over_prefix():
    client = _client_with([
        _fake_container("climweb"),
        _fake_container("climweb_db"),
    ])
    with mock.patch.object(docker_client, "get_client", return_value=client):
        names = [c["name"] for c in docker_client.list_containers(use_cache=False)]

    assert names == ["climweb"]


@override_settings(
    CLIMWEB_LOG_VIEWER_ENABLED=True,
    CLIMWEB_DOCKER_HOST="tcp://climweb_docker_proxy:2375",
    CLIMWEB_LOG_VIEWER_CONTAINERS=["climweb"],
)
def test_disallowed_container_is_rejected_before_any_docker_call():
    client = _client_with([_fake_container("climweb")])
    with mock.patch.object(docker_client, "get_client", return_value=client):
        with pytest.raises(docker_client.LogViewerError):
            docker_client.resolve_container("some_other_container")

    client.containers.get.assert_not_called()


@override_settings(CLIMWEB_LOG_VIEWER_ENABLED=False)
def test_disabled_instance_refuses_to_build_a_client():
    with pytest.raises(docker_client.LogViewerDisabled):
        docker_client.get_client()


@override_settings(CLIMWEB_LOG_VIEWER_ENABLED=True, CLIMWEB_DOCKER_HOST="")
def test_missing_docker_host_is_treated_as_disabled():
    with pytest.raises(docker_client.LogViewerDisabled):
        docker_client.get_client()


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------

@override_settings(
    CLIMWEB_LOG_VIEWER_ENABLED=True,
    CLIMWEB_DOCKER_HOST="tcp://climweb_docker_proxy:2375",
    CLIMWEB_LOG_VIEWER_CONTAINERS=["climweb"],
)
def test_fetch_logs_parses_and_redacts():
    container = _fake_container("climweb")
    container.logs.return_value = (
        b"2026-07-31T09:15:00.000000001Z INFO started\n"
        b"2026-07-31T09:15:01.000000001Z ERROR bad key leaked-secret-value\n"
    )
    client = _client_with([container])
    client.containers.get.return_value = container

    env = {"SECRET_KEY": "leaked-secret-value"}
    with mock.patch.object(docker_client, "get_client", return_value=client), \
            mock.patch.dict(docker_client.os.environ, env, clear=True):
        lines = docker_client.fetch_logs("climweb", tail=10)

    assert len(lines) == 2
    assert lines[0]["level"] == "INFO"
    assert lines[1]["level"] == "ERROR"
    assert "leaked-secret-value" not in lines[1]["message"]
    assert container.logs.call_args.kwargs["timestamps"] is True


@override_settings(
    CLIMWEB_LOG_VIEWER_ENABLED=True,
    CLIMWEB_DOCKER_HOST="tcp://climweb_docker_proxy:2375",
    CLIMWEB_LOG_VIEWER_CONTAINERS=["climweb"],
)
def test_tail_is_clamped_to_max_lines():
    container = _fake_container("climweb")
    container.logs.return_value = b""
    client = _client_with([container])
    client.containers.get.return_value = container

    with mock.patch.object(docker_client, "get_client", return_value=client):
        docker_client.fetch_logs("climweb", tail=10_000_000, max_lines=500)

    assert container.logs.call_args.kwargs["tail"] == 500


@override_settings(
    CLIMWEB_LOG_VIEWER_ENABLED=True,
    CLIMWEB_DOCKER_HOST="tcp://climweb_docker_proxy:2375",
    CLIMWEB_LOG_VIEWER_CONTAINERS=["climweb"],
)
def test_since_is_passed_as_a_datetime_one_second_early():
    """Docker's `since` has one-second granularity; over-fetch and dedupe."""
    container = _fake_container("climweb")
    container.logs.return_value = b""
    client = _client_with([container])
    client.containers.get.return_value = container

    with mock.patch.object(docker_client, "get_client", return_value=client):
        docker_client.fetch_logs("climweb", since="2026-07-31T09:15:10.500000000Z")

    since = container.logs.call_args.kwargs["since"]
    assert since.year == 2026 and since.second == 9


@override_settings(
    CLIMWEB_LOG_VIEWER_ENABLED=True,
    CLIMWEB_DOCKER_HOST="tcp://climweb_docker_proxy:2375",
    CLIMWEB_LOG_VIEWER_CONTAINERS=["climweb"],
)
def test_unparseable_since_falls_back_to_tail():
    container = _fake_container("climweb")
    container.logs.return_value = b""
    client = _client_with([container])
    client.containers.get.return_value = container

    with mock.patch.object(docker_client, "get_client", return_value=client):
        docker_client.fetch_logs("climweb", tail=42, since="not-a-timestamp")

    assert "since" not in container.logs.call_args.kwargs
    assert container.logs.call_args.kwargs["tail"] == 42


@override_settings(
    CLIMWEB_LOG_VIEWER_ENABLED=True,
    CLIMWEB_DOCKER_HOST="tcp://climweb_docker_proxy:2375",
    CLIMWEB_LOG_VIEWER_CONTAINERS=["climweb"],
)
def test_docker_errors_become_friendly_messages():
    container = _fake_container("climweb")
    container.logs.side_effect = RuntimeError("connection refused")
    client = _client_with([container])
    client.containers.get.return_value = container

    with mock.patch.object(docker_client, "get_client", return_value=client):
        with pytest.raises(docker_client.LogViewerError, match="connection refused"):
            docker_client.fetch_logs("climweb")


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_non_superuser_cannot_reach_the_log_endpoints(client, django_user_model):
    editor = django_user_model.objects.create_user(
        username="editor", password="pw12345!", is_staff=True
    )
    client.force_login(editor)

    for name in ("log-viewer", "log-fetch", "log-download"):
        from django.urls import reverse

        response = client.get(reverse(name), {"container": "climweb"})
        assert response.status_code == 403, name


@pytest.mark.django_db
@override_settings(
    CLIMWEB_LOG_VIEWER_ENABLED=True,
    CLIMWEB_DOCKER_HOST="tcp://climweb_docker_proxy:2375",
    CLIMWEB_LOG_VIEWER_CONTAINERS=["climweb"],
)
def test_fetch_drops_lines_the_client_already_has(client, django_user_model):
    from django.urls import reverse

    admin = django_user_model.objects.create_superuser(
        username="admin", password="pw12345!", email="a@example.com"
    )
    client.force_login(admin)

    returned = [
        {"ts": "2026-07-31T09:15:00.000000001Z", "level": "INFO", "message": "old"},
        {"ts": "2026-07-31T09:15:09.000000001Z", "level": "INFO", "message": "new"},
    ]
    with mock.patch.object(docker_client, "fetch_logs", return_value=returned), \
            mock.patch("climweb.base.logs.views.fetch_logs", return_value=returned):
        response = client.get(
            reverse("log-fetch"),
            {"container": "climweb", "since": "2026-07-31T09:15:05.000000000Z"},
        )

    payload = response.json()
    assert [line["message"] for line in payload["lines"]] == ["new"]
    assert payload["latest"] == "2026-07-31T09:15:09.000000001Z"
