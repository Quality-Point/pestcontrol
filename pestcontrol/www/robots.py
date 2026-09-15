# Copyright (c) 2026, QualityPoint and contributors
# For license information, please see license.txt

"""Overrides frappe's /robots.txt.

Frappe's own version (frappe/www/robots.py) just echoes whatever text is
typed into Website Settings.robots_txt -- nothing in the repo drives it, it
has no Sitemap: pointer, and it has no awareness of the customer-portal
cluster. This generates it from the same PC Website Settings.canonical_base_url
used by sitemap.py, and blocks the private/account paths a crawler has no
business indexing -- website permission checks already keep them out of
reach, this is about crawl budget, not access control.

The app's copy wins over frappe's for the same reason pestcontrol/www/
sitemap.py's does: both the jinja loader and TemplatePage.set_template_path
walk reversed(get_installed_apps()), and pestcontrol installs after frappe.
"""

import frappe
from frappe.utils import get_url

no_cache = 1

# Kept as an explicit list rather than reusing pc_website/router.py's
# FRAMEWORK_ROOTS/_claimed_roots(): that set also includes "project", which
# must stay crawlable at /project/<slug> (the public Website Project
# generator pages) even though /project itself is erpnext's login-walled
# portal list -- a shared list would block both. pestcontrol/www/sitemap.py's
# own EXCLUDE set is maintained separately from router.py for the same reason.
DISALLOW = (
	"/app/",
	"/api/",
	"/login",
	"/update-password",
	"/portal",
	"/me",
	"/orders",
	"/quotations",
	"/invoices",
	"/addresses",
	"/shipments",
)


def get_context(context):
	settings = frappe.get_cached_doc("PC Website Settings")
	base = (settings.get("canonical_base_url") or get_url()).rstrip("/")
	return {"disallow": DISALLOW, "sitemap_url": f"{base}/sitemap.xml"}
