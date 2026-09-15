# Copyright (c) 2026, QualityPoint and contributors
# For license information, please see license.txt

"""Language-prefixed public URLs: /ar/about, /en/about.

Frappe serves every language from one URL, choosing by cookie. A crawler
carries no cookie, so exactly one language is ever indexed -- on this site
that is english, leaving the entire arabic catalogue invisible in the primary
market. Frappe has no multi-language URL support of its own, so this is ours.

Registered as `website_path_resolver`, which REPLACES frappe's own
resolve_path() call inside PathResolver.resolve(). Two consequences:

  * frappe's werkzeug RequestRedirect handling goes with it, so _delegate()
    re-raises it as frappe.Redirect.
  * There is no `endpoint == "app"` shortcut in frappe 16 -- only `desk` is
    short-circuited before the hooks. /app reaches this function, so a bug
    here takes down the desk as well as the website. The reserved check is
    deliberately the first branch, and this hook can be disabled by deleting
    one line from hooks.py plus `bench clear-cache`.
"""

import frappe
import werkzeug.routing.exceptions
from frappe.website.path_resolver import resolve_path

from pestcontrol.pc_website.utils import get_site_languages

# Framework and machine-readable paths that no language prefix may touch.
# The portal cluster is NOT listed here -- it is derived from the site's own
# website_route_rules in _reserved_roots(), so an erpnext upgrade that adds a
# portal route does not silently start prefixing it.
FRAMEWORK_ROOTS = frozenset(
	(
		"app",
		"api",
		"assets",
		"files",
		"private",
		"backups",
		"socketio",
		"printview",
		"print",
		"method",
		"login",
		"update-password",
		"signup",
		"verify-email",
		"third_party",
		".well-known",
		"desk",
		# The customer portal and /me are plain www pages rather than route
		# rules, so _claimed_roots() never sees them. erpnext's ListPage forces
		# app="frappe" for the portal cluster, and none of it is content a search
		# engine should be reaching in the first place.
		"portal",
		"me",
	)
)
RESERVED_EXACT = frozenset(
	(
		"sitemap.xml",
		"robots.txt",
		"favicon.ico",
		"manifest.json",
		"website_script.js",
		# Google Search Console's HTML-file verification method requires this
		# exact file to return 200 at the bare root, with no redirect -- a
		# language-prefixed 301 fails verification outright.
		"google04549cf1f9632b2c.html",
	)
)


def resolve(path):
	"""`website_path_resolver` hook. Returns the endpoint to render."""
	path = (path or "").strip("/ ")
	first = path.split("/", 1)[0].lower()

	# Defaults for the jinja helpers, overwritten below when a prefix applies.
	frappe.local.pc_lang = None
	frappe.local.pc_prefix = ""
	frappe.local.pc_bare_path = path

	if _is_reserved(path, first):
		return _delegate(path)

	languages = {row["code"] for row in get_site_languages()}

	if first in languages:
		rest = path[len(first) :].strip("/")
		frappe.local.lang = first
		frappe.local.pc_lang = first
		frappe.local.pc_prefix = "/" + first
		frappe.local.pc_bare_path = rest
		if not rest:
			# /ar/ is the marketing home for everyone. get_home_page() would
			# consult Role home pages and Portal Settings and could send a
			# logged-in customer to the portal -- but this is the indexable
			# homepage, and it must show a crawler what it shows a person.
			return (frappe.get_hooks("home_page") or ["home"])[-1]

		if _is_reserved(rest, rest.split("/", 1)[0].lower()):
			# A reserved path wearing a language prefix: /en/desk, /ar/orders,
			# /en/api/method/ping. Nothing links to these, but they are
			# reachable by hand and by a crawler following a mangled link, and
			# serving them would mint a second URL for every framework and
			# portal page. /en/desk also breaks outright, because frappe's own
			# desk shortcut runs before this hook and only matches a bare
			# "desk". Send them to the one place they belong.
			frappe.flags.redirect_location = "/" + rest + _query_suffix()
			raise frappe.Redirect(301)

		return _delegate(rest)

	# Unprefixed public path: send it to a language prefix, permanently.
	target = "/" + _target_language(languages) + ("/" + path if path else "/")
	frappe.flags.redirect_location = target + _query_suffix()
	raise frappe.Redirect(301)


def u(path=""):
	"""Language-prefixed URL for a template link.

	Registered as a jinja method, so templates say href="{{ u('/about') }}"
	instead of href="/about" and every internal link keeps the visitor in the
	language they are reading. Reserved and portal routes pass through
	unprefixed -- /portal must not become /ar/portal.
	"""
	path = "/" + (path or "").lstrip("/")
	bare = path.strip("/")
	first = bare.split("/", 1)[0].lower()
	if bare and _is_reserved(bare, first):
		return path
	prefix = getattr(frappe.local, "pc_prefix", "") or ""
	if not prefix:
		# Rendered outside a prefixed request (a job, a test, the portal):
		# fall back to the configured default so links are never bare.
		languages = {row["code"] for row in get_site_languages()}
		prefix = "/" + _default_language(languages)
	return prefix + path


def _is_reserved(path, first):
	"""True when `path` must be served without a language prefix.

	A root claimed by website_route_rules is reserved *unless* we own that
	prefix and the path goes deeper than one segment. That distinction exists
	for exactly one real collision: erpnext claims /project for its portal
	list, while Website Project generates /project/<slug>. Both are valid, so
	the bare route stays erpnext's and the deeper one is ours.
	"""
	if first in FRAMEWORK_ROOTS or path in RESERVED_EXACT:
		return True
	if first not in _claimed_roots():
		return False
	return not (first in _generator_roots() and "/" in path)


def _claimed_roots():
	"""First path segment of every website_route_rule on the site."""
	return {
		rule["from_route"].strip("/").split("/")[0].lower()
		for rule in (frappe.get_hooks("website_route_rules") or [])
		if rule.get("from_route")
	}


def _generator_roots():
	"""Route prefixes owned by this app's website generators."""
	roots = set()
	for doctype in frappe.get_hooks("website_generators") or []:
		route = (frappe.get_meta(doctype).route or "").strip("/")
		if route:
			roots.add(route.split("/")[0].lower())
	return roots


def _target_language(languages):
	"""Language to redirect an unprefixed path to.

	`?_lang=xx` wins, so links the old cookie-based switcher put into the wild
	land on the page they meant. Varying on a query param is safe -- it is part
	of the URL, so caches see two distinct URLs. Varying on the *cookie* would
	not be: that redirect is uncacheable by any CDN, and a crawler must always
	get one stable target. Hence the cookie is never consulted here.
	"""
	requested = frappe.form_dict.get("_lang") if frappe.form_dict else None
	if requested in languages:
		return requested
	return _default_language(languages)


def _default_language(languages):
	"""Language served at the site root -- a desk setting, never a constant."""
	configured = frappe.db.get_single_value("PC Website Settings", "default_language")
	if configured in languages:
		return configured
	return frappe.local.lang if frappe.local.lang in languages else "en"


def _query_suffix():
	"""Preserve the query string across the redirect, minus `_lang`.

	_target_language() has already read `_lang` to pick the destination, so it
	is stripped here: the prefix now carries that meaning, and leaving the param
	on a prefixed URL would fragment it into a duplicate.
	"""
	query = frappe.local.request.query_string if getattr(frappe.local, "request", None) else None
	if not query:
		return ""
	from urllib.parse import parse_qsl, urlencode

	kept = [(k, v) for k, v in parse_qsl(frappe.safe_decode(query)) if k != "_lang"]
	return "?" + urlencode(kept) if kept else ""


def _delegate(path):
	"""Hand a bare path to frappe's own resolver.

	Registering website_path_resolver replaces frappe's resolve_path() call
	*including* the RequestRedirect handling that normally wraps it, so that
	is reproduced here.
	"""
	try:
		return resolve_path(path)
	except werkzeug.routing.exceptions.RequestRedirect as e:
		frappe.flags.redirect_location = e.new_url
		raise frappe.Redirect(e.code)
