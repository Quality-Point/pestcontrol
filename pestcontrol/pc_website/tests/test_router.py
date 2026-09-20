# Copyright (c) 2026, QualityPoint and contributors
# For license information, please see license.txt

"""Tests for the language-prefix resolver.

These matter more than most. `website_path_resolver` replaces frappe's own
path resolution for *every* request, and frappe 16 short-circuits only `desk`
before the hooks -- there is no `endpoint == "app"` shortcut -- so /app, /api
and the customer portal all pass through resolve(). A regression here takes
down the desk, not just the website.

Route rules only evaluate when a request is bound (evaluate_dynamic_routes
checks frappe.local.request), so every case binds a real werkzeug request.
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request

from pestcontrol.pc_website.router import resolve
from pestcontrol.pc_website.seo import build_seo_context


def _bind(path, query=""):
	full = "/" + path.lstrip("/") + (f"?{query}" if query else "")
	frappe.local.request = Request(EnvironBuilder(path=full).get_environ())
	frappe.local.form_dict = frappe._dict(
		{k: v for k, v in (p.split("=", 1) for p in query.split("&") if "=" in p)}
	)


class TestLanguageRouter(FrappeTestCase):
	def setUp(self):
		frappe.local.lang = "en"

	# -- paths that must never be touched ---------------------------------

	def test_framework_paths_pass_through_unchanged(self):
		"""A redirect here would break the desk and the API."""
		for path in (
			"app",
			"app/website-service",
			"api/method/ping",
			"assets/pestcontrol/website/css/custom.css",
			"files/example.png",
			"private/files/x.png",
			"login",
		):
			with self.subTest(path=path):
				_bind(path)
				try:
					resolve(path)  # must not raise Redirect
				except frappe.Redirect:
					self.fail(f"/{path} was redirected; the desk or API would break")
				self.assertEqual(frappe.local.pc_prefix, "")

	def test_machine_readable_paths_pass_through(self):
		for path in ("sitemap.xml", "robots.txt", "favicon.ico"):
			with self.subTest(path=path):
				_bind(path)
				try:
					resolve(path)
				except frappe.Redirect:
					self.fail(f"/{path} must not be language-prefixed")

	def test_portal_cluster_is_not_prefixed(self):
		"""Derived from the site's own website_route_rules, not hardcoded."""
		for path in ("orders", "invoices", "quotations", "addresses", "tasks"):
			with self.subTest(path=path):
				_bind(path)
				try:
					resolve(path)
				except frappe.Redirect:
					self.fail(f"/{path} is a portal route and must stay unprefixed")

	# -- the /project collision -------------------------------------------

	def test_bare_project_belongs_to_erpnext(self):
		"""erpnext claims /project for its portal list."""
		_bind("project")
		try:
			resolve("project")
		except frappe.Redirect:
			self.fail("/project is erpnext's portal list and must stay unprefixed")

	def test_project_detail_belongs_to_us(self):
		"""Website Project generates /project/<slug>, which we do prefix."""
		_bind("project/some-slug")
		try:
			resolve("project/some-slug")
		except frappe.Redirect:
			self.fail("/project/some-slug is ours and must render directly, not redirect")
		self.assertEqual(frappe.local.pc_prefix, f"/{self._default()}")

	# -- unprefixed paths render the default language directly ------------

	def test_root_serves_default_language_directly(self):
		_bind("")
		try:
			endpoint = resolve("")
		except frappe.Redirect:
			self.fail("/ must render directly, not redirect")
		self.assertEqual(endpoint, (frappe.get_hooks("home_page") or ["home"])[-1])
		self.assertEqual(frappe.local.lang, self._default())
		self.assertEqual(frappe.local.pc_prefix, f"/{self._default()}")
		self.assertEqual(frappe.local.pc_bare_path, "")

	def test_unprefixed_page_serves_default_language_directly(self):
		_bind("about")
		try:
			endpoint = resolve("about")
		except frappe.Redirect:
			self.fail("/about must render directly, not redirect")
		self.assertEqual(endpoint, "about")
		self.assertEqual(frappe.local.lang, self._default())
		self.assertEqual(frappe.local.pc_prefix, f"/{self._default()}")
		self.assertEqual(frappe.local.pc_bare_path, "about")

	def test_bare_and_prefixed_home_render_identically(self):
		_bind("")
		bare_endpoint = resolve("")
		bare_lang = frappe.local.lang
		_bind(f"{self._default()}/")
		prefixed_endpoint = resolve(f"{self._default()}/")
		self.assertEqual(bare_endpoint, prefixed_endpoint)
		self.assertEqual(bare_lang, frappe.local.lang)

	def test_lang_query_param_picks_the_target_and_is_dropped(self):
		"""Migration shim for URLs the old cookie switcher left in the wild."""
		_bind("about", "_lang=en")
		with self.assertRaises(frappe.Redirect):
			resolve("about")
		self.assertEqual(frappe.flags.redirect_location, "/en/about")

	def test_other_query_params_survive_the_redirect(self):
		_bind("about", "_lang=ar&utm_source=google")
		with self.assertRaises(frappe.Redirect):
			resolve("about")
		self.assertIn("utm_source=google", frappe.flags.redirect_location)

	# -- prefixed paths resolve ------------------------------------------

	def test_prefixed_root_is_the_marketing_home(self):
		"""Never the role/portal home, even for a logged-in user."""
		_bind("ar/")
		endpoint = resolve("ar/")
		self.assertEqual(endpoint, (frappe.get_hooks("home_page") or ["home"])[-1])
		self.assertEqual(frappe.local.lang, "ar")
		self.assertEqual(frappe.local.pc_prefix, "/ar")

	def test_prefix_sets_language_and_strips_itself(self):
		for lang in ("ar", "en"):
			with self.subTest(lang=lang):
				_bind(f"{lang}/about")
				endpoint = resolve(f"{lang}/about")
				self.assertEqual(endpoint, "about")
				self.assertEqual(frappe.local.lang, lang)
				self.assertEqual(frappe.local.pc_prefix, f"/{lang}")
				self.assertEqual(frappe.local.pc_bare_path, "about")

	def test_prefixed_generator_route_resolves(self):
		route = frappe.db.get_value("Website Service", {"published": 1}, "route")
		if not route:
			self.skipTest("no published Website Service on this site")
		_bind(f"ar/{route}")
		self.assertEqual(resolve(f"ar/{route}"), route)
		self.assertEqual(frappe.local.lang, "ar")

	def test_reserved_path_under_a_prefix_redirects_away(self):
		"""/en/desk and friends must not become second URLs for framework pages.

		Regression: the prefix was stripped and the remainder delegated without
		re-checking it, so /en/app, /ar/orders and /en/api/... were all served
		under a language prefix. /en/desk broke outright, because frappe's own
		desk shortcut runs before this hook and only matches a bare "desk".
		"""
		for path, expected in (
			("en/desk", "/desk"),
			("ar/desk", "/desk"),
			("en/app", "/app"),
			("ar/api/method/ping", "/api/method/ping"),
			("en/portal", "/portal"),
			("ar/orders", "/orders"),
			("en/assets/pestcontrol/website/css/custom.css", "/assets/pestcontrol/website/css/custom.css"),
		):
			with self.subTest(path=path):
				_bind(path)
				with self.assertRaises(frappe.Redirect):
					resolve(path)
				self.assertEqual(frappe.flags.redirect_location, expected)

	def test_unknown_prefixed_path_is_not_redirected(self):
		"""It should 404 through the normal renderers, not bounce."""
		_bind("ar/does-not-exist")
		try:
			resolve("ar/does-not-exist")
		except frappe.Redirect:
			self.fail("a missing page under a prefix must 404, not redirect")

	# -- direct-serve stays indexable via canonical/hreflang ---------------

	def test_bare_path_canonicalizes_to_prefixed_url(self):
		_bind("about")
		resolve("about")
		context = self._seo_context("about")
		self.assertTrue(context.seo_canonical.endswith(f"/{self._default()}/about"))
		langs = {alt.lang for alt in context.seo_alternates}
		self.assertIn(self._default(), langs)

	def test_bare_root_canonicalizes_to_prefixed_home(self):
		_bind("")
		resolve("")
		context = self._seo_context("")
		self.assertTrue(context.seo_canonical.endswith(f"/{self._default()}/"))

	def _seo_context(self, route):
		settings = frappe.get_cached_doc("PC Website Settings").as_dict()
		context = frappe._dict(route=route, settings=settings)
		build_seo_context(context)
		return context

	def _default(self):
		langs = {
			r["code"] for r in frappe.get_all("Language", filters={"enabled": 1}, fields=["name as code"])
		}
		configured = frappe.db.get_single_value("PC Website Settings", "default_language")
		return configured if configured in langs else "en"
