"""
Tests for the product sync API.

The path-traversal and format cases here are the ones that matter: the upload
endpoint takes a caller-supplied path and writes a file with it, so a gap there
is an arbitrary write on the ClimWeb server.
"""

import os
import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.utils import timezone

from climweb.base.models import Product, ProductCategory
from climweb.pages.products.sync_api import safe_destination
from climweb.pages.products.sync_models import (
    ProductSyncCredential,
    ProductSyncSetupCode,
    normalise_setup_code,
)


class SafeDestinationTests(TestCase):
    """The containment rule, tested directly."""

    def setUp(self):
        self.base = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)

    def test_accepts_a_plain_filename(self):
        result = safe_destination(self.base, "bulletin_09-03-2026.pdf")
        self.assertEqual(result, os.path.join(self.base, "bulletin_09-03-2026.pdf"))

    def test_accepts_a_year_subdirectory(self):
        result = safe_destination(self.base, "2026/bulletin.pdf")
        self.assertEqual(result, os.path.join(self.base, "2026", "bulletin.pdf"))

    def test_rejects_parent_traversal(self):
        for candidate in [
            "../evil.pdf",
            "../../etc/passwd",
            "2026/../../evil.pdf",
            "a/b/../../../evil.pdf",
        ]:
            with self.subTest(candidate=candidate):
                self.assertIsNone(safe_destination(self.base, candidate))

    def test_rejects_absolute_paths(self):
        for candidate in ["/etc/passwd", "//etc/passwd", "/tmp/evil.pdf"]:
            with self.subTest(candidate=candidate):
                self.assertIsNone(safe_destination(self.base, candidate))

    def test_rejects_backslash_traversal(self):
        self.assertIsNone(safe_destination(self.base, "..\\..\\evil.pdf"))

    def test_rejects_dotfiles(self):
        for candidate in [".htaccess", ".ssh/authorized_keys", "sub/.env"]:
            with self.subTest(candidate=candidate):
                self.assertIsNone(safe_destination(self.base, candidate))

    def test_rejects_empty_paths(self):
        for candidate in ["", "/", "./", "."]:
            with self.subTest(candidate=candidate):
                self.assertIsNone(safe_destination(self.base, candidate))

    def test_rejects_a_symlink_that_escapes(self):
        outside = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        os.symlink(outside, os.path.join(self.base, "escape"))
        self.assertIsNone(safe_destination(self.base, "escape/evil.pdf"))


class SetupCodeTests(TestCase):
    def test_normalisation_is_forgiving_about_formatting(self):
        canonical = "K7FA-2C9D-TX43"
        for typed in [
            "K7FA-2C9D-TX43",
            "k7fa-2c9d-tx43",
            "K7FA2C9DTX43",
            "  k7fa 2c9d tx43  ",
        ]:
            with self.subTest(typed=typed):
                self.assertEqual(normalise_setup_code(typed), canonical)

    def test_wrong_length_is_rejected(self):
        self.assertEqual(normalise_setup_code("K7FA-2C9D"), "")
        self.assertEqual(normalise_setup_code(""), "")
        self.assertEqual(normalise_setup_code(None), "")

    def test_generated_codes_avoid_ambiguous_characters(self):
        from climweb.pages.products.sync_models import generate_setup_code

        for _ in range(200):
            code = generate_setup_code()
            self.assertNotRegex(code, r"[O0I1LS58BU]")


class SyncApiTestCase(TestCase):
    """Shared fixtures: a product with a real, temporary watch root."""

    def setUp(self):
        self.watch_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.watch_root, ignore_errors=True)

        self.product = Product.objects.create(
            name="Weekly Rainfall",
            variable_name="weekly_rainfall",
            watch_root=self.watch_root,
            ingestion_enabled=True,
        )
        ProductCategory.objects.create(
            product=self.product, name="Bulletin", category_format="pdf"
        )
        self.client = Client()

    def issue_credential(self):
        return ProductSyncCredential.issue(self.product, "met-server.example.org")

    def auth(self, token):
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def upload(self, token, **overrides):
        from django.core.files.uploadedfile import SimpleUploadedFile

        payload = {
            "variable_name": "weekly_rainfall",
            "format": "pdf",
            "relative_path": "bulletin.pdf",
            "file": SimpleUploadedFile("bulletin.pdf", b"%PDF-1.4 test"),
        }
        payload.update(overrides)
        return self.client.post(
            "/api/product-sync/upload/", payload, **self.auth(token)
        )


class SetupExchangeTests(SyncApiTestCase):
    def test_a_valid_code_returns_settings_and_a_token(self):
        code = ProductSyncSetupCode.issue(self.product)
        response = self.client.post(
            "/api/product-sync/setup/exchange/",
            {"code": code.code, "hostname": "met-server"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["variable_name"], "weekly_rainfall")
        self.assertEqual(body["format"], "pdf")
        self.assertTrue(body["token"])

        # The operator is never asked for the destination, so it must be right.
        self.assertEqual(body["watch_root"], self.watch_root)

    def test_env_format_is_shell_safe(self):
        self.product.name = "It's \"Weekly\" Rainfall"
        self.product.save()
        code = ProductSyncSetupCode.issue(self.product)
        response = self.client.post(
            "/api/product-sync/setup/exchange/",
            {"code": code.code, "hostname": "met", "format": "env"},
        )
        self.assertEqual(response.status_code, 200)
        text = response.content.decode()
        # A naive implementation would break out of the quoting here, and the
        # client sources this response directly.
        self.assertIn("'\\''", text)
        self.assertNotIn("\n\n", text)

    def test_a_code_works_only_once(self):
        code = ProductSyncSetupCode.issue(self.product)
        first = self.client.post(
            "/api/product-sync/setup/exchange/", {"code": code.code}
        )
        self.assertEqual(first.status_code, 200)
        second = self.client.post(
            "/api/product-sync/setup/exchange/", {"code": code.code}
        )
        self.assertEqual(second.status_code, 403)

    def test_an_expired_code_is_refused(self):
        code = ProductSyncSetupCode.issue(self.product)
        code.expires_at = timezone.now() - timezone.timedelta(minutes=1)
        code.save()
        response = self.client.post(
            "/api/product-sync/setup/exchange/", {"code": code.code}
        )
        self.assertEqual(response.status_code, 403)

    def test_issuing_a_new_code_retires_the_previous_one(self):
        old = ProductSyncSetupCode.issue(self.product)
        ProductSyncSetupCode.issue(self.product)
        response = self.client.post(
            "/api/product-sync/setup/exchange/", {"code": old.code}
        )
        self.assertEqual(response.status_code, 403)

    def test_an_unknown_code_is_refused(self):
        response = self.client.post(
            "/api/product-sync/setup/exchange/", {"code": "AAAA-AAAA-AAAA"}
        )
        self.assertEqual(response.status_code, 403)

    def test_a_product_with_no_variable_name_reports_why(self):
        self.product.variable_name = ""
        self.product.save()
        code = ProductSyncSetupCode.issue(self.product)
        response = self.client.post(
            "/api/product-sync/setup/exchange/", {"code": code.code}
        )
        self.assertEqual(response.status_code, 409)
        self.assertIn("Variable Name", response.json()["detail"])


class UploadTests(SyncApiTestCase):
    def test_a_valid_upload_lands_where_the_ingester_looks(self):
        _, token = self.issue_credential()
        response = self.upload(token, relative_path="2026/bulletin.pdf")
        self.assertEqual(response.status_code, 201)

        expected = os.path.join(
            self.watch_root, "weekly_rainfall", "pdf", "2026", "bulletin.pdf"
        )
        self.assertTrue(os.path.exists(expected))
        with open(expected, "rb") as handle:
            self.assertEqual(handle.read(), b"%PDF-1.4 test")

    def test_uploaded_files_are_readable_by_the_ingester(self):
        _, token = self.issue_credential()
        self.upload(token)
        path = os.path.join(self.watch_root, "weekly_rainfall", "pdf", "bulletin.pdf")
        self.assertEqual(os.stat(path).st_mode & 0o777, 0o644)

    def test_replacing_a_file_reports_200(self):
        _, token = self.issue_credential()
        self.assertEqual(self.upload(token).status_code, 201)
        self.assertEqual(self.upload(token).status_code, 200)

    def test_no_partial_files_are_left_behind(self):
        _, token = self.issue_credential()
        self.upload(token)
        directory = os.path.join(self.watch_root, "weekly_rainfall", "pdf")
        leftovers = [n for n in os.listdir(directory) if n.startswith(".upload-")]
        self.assertEqual(leftovers, [])

    def test_traversal_is_refused(self):
        _, token = self.issue_credential()
        for candidate in ["../../evil.pdf", "/etc/evil.pdf", "a/../../evil.pdf"]:
            with self.subTest(candidate=candidate):
                response = self.upload(token, relative_path=candidate)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["error"], "bad_path")

    def test_an_extension_that_contradicts_the_format_is_refused(self):
        _, token = self.issue_credential()
        response = self.upload(token, relative_path="evil.php")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "bad_extension")

    def test_a_format_the_product_does_not_use_is_refused(self):
        _, token = self.issue_credential()
        response = self.upload(token, format="png", relative_path="x.png")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "bad_format")

    def test_a_token_cannot_write_to_another_product(self):
        _, token = self.issue_credential()
        response = self.upload(token, variable_name="something_else")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "wrong_product")

    def test_no_token_is_refused(self):
        response = self.client.post("/api/product-sync/upload/", {})
        self.assertEqual(response.status_code, 401)

    def test_a_revoked_token_stops_working(self):
        credential, token = self.issue_credential()
        self.assertEqual(self.upload(token).status_code, 201)
        credential.revoke()
        self.assertEqual(self.upload(token).status_code, 401)

    def test_tokens_are_not_stored_in_the_clear(self):
        credential, token = self.issue_credential()
        self.assertNotIn(token, credential.token_hash)
        self.assertNotEqual(credential.token_hash, token)

    @override_settings(PRODUCT_SYNC_MAX_UPLOAD_BYTES=10)
    def test_an_oversized_file_reports_413(self):
        _, token = self.issue_credential()
        from django.core.files.uploadedfile import SimpleUploadedFile

        response = self.upload(
            token, file=SimpleUploadedFile("big.pdf", b"x" * 100)
        )
        self.assertEqual(response.status_code, 413)

    def test_upload_count_is_recorded(self):
        credential, token = self.issue_credential()
        self.upload(token)
        credential.refresh_from_db()
        self.assertEqual(credential.upload_count, 1)
        self.assertIsNotNone(credential.last_used_at)


class PingTests(SyncApiTestCase):
    def test_a_valid_token_is_accepted(self):
        _, token = self.issue_credential()
        response = self.client.get("/api/product-sync/ping/", **self.auth(token))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["variable_name"], "weekly_rainfall")

    def test_a_bad_token_is_refused(self):
        response = self.client.get(
            "/api/product-sync/ping/", **self.auth("not-a-real-token")
        )
        self.assertEqual(response.status_code, 401)


class FullSyncRequestTests(SyncApiTestCase):
    """
    The 'Sync all files' button in the admin.

    Nothing can be pushed to the source server, so the request rides along on
    the ping the client already makes, and is cleared only once the client
    reports back.
    """

    def test_ping_reports_no_request_by_default(self):
        _, token = self.issue_credential()
        response = self.client.get("/api/product-sync/ping/", **self.auth(token))
        self.assertEqual(response.json()["full_sync_requested"], "false")

    def test_ping_reports_a_pending_request(self):
        credential, token = self.issue_credential()
        credential.request_full_sync()
        response = self.client.get("/api/product-sync/ping/", **self.auth(token))
        self.assertEqual(response.json()["full_sync_requested"], "true")

    def test_the_env_form_carries_the_flag(self):
        credential, token = self.issue_credential()
        credential.request_full_sync()
        response = self.client.get(
            "/api/product-sync/ping/?format=env", **self.auth(token)
        )
        self.assertIn("FULL_SYNC_REQUESTED='true'", response.content.decode())

    def test_reading_the_flag_does_not_clear_it(self):
        """A run that dies after pinging must still get its full sync."""
        credential, token = self.issue_credential()
        credential.request_full_sync()

        self.client.get("/api/product-sync/ping/", **self.auth(token))
        credential.refresh_from_db()
        self.assertTrue(credential.full_sync_pending)

        response = self.client.get("/api/product-sync/ping/", **self.auth(token))
        self.assertEqual(response.json()["full_sync_requested"], "true")

    def test_the_client_clears_it_on_completion(self):
        credential, token = self.issue_credential()
        credential.request_full_sync()

        response = self.client.post(
            "/api/product-sync/full-sync-complete/", {}, **self.auth(token)
        )
        self.assertEqual(response.status_code, 200)

        credential.refresh_from_db()
        self.assertFalse(credential.full_sync_pending)
        self.assertIsNotNone(credential.full_sync_completed_at)

    def test_completion_without_a_request_is_harmless(self):
        credential, token = self.issue_credential()
        response = self.client.post(
            "/api/product-sync/full-sync-complete/", {}, **self.auth(token)
        )
        self.assertEqual(response.status_code, 200)
        credential.refresh_from_db()
        self.assertIsNone(credential.full_sync_completed_at)

    def test_completion_needs_a_valid_token(self):
        response = self.client.post(
            "/api/product-sync/full-sync-complete/", {}, **self.auth("nope")
        )
        self.assertEqual(response.status_code, 401)

    def test_one_server_cannot_clear_anothers_request(self):
        first, _ = self.issue_credential()
        _, second_token = self.issue_credential()
        first.request_full_sync()

        self.client.post(
            "/api/product-sync/full-sync-complete/", {}, **self.auth(second_token)
        )

        first.refresh_from_db()
        self.assertTrue(first.full_sync_pending)

    def test_a_request_can_be_cancelled(self):
        credential, _ = self.issue_credential()
        credential.request_full_sync()
        credential.cancel_full_sync()
        credential.refresh_from_db()
        self.assertFalse(credential.full_sync_pending)


class SetupScriptTests(TestCase):
    def test_the_bootstrap_script_is_served(self):
        response = self.client.get("/api/product-sync/setup.sh")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertTrue(body.startswith("#!/usr/bin/env bash"))
        self.assertIn("climweb-sync setup", body)
        # It must refuse to run without a code rather than doing something
        # surprising.
        self.assertIn('if [ -z "$CODE" ]', body)
