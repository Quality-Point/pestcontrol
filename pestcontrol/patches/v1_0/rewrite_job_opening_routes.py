# Copyright (c) 2026, QualityPoint and contributors
# For license information, please see license.txt

"""Move existing Job Openings from HRMS's `jobs/<company>/<slug>` routes onto
`careers/<slug>`, so every opening lives inside the careers section that now
lists and serves them.

Goes through doc.save() rather than a direct db write: clearing `route` makes
PCJobOpening.validate rebuild it, which keeps the uniqueness loop, the
reserved-slug guard and the length cap in one place instead of duplicating
them here.

Idempotent: a route already under `careers/` is left alone.
"""

import frappe
from frappe.website.utils import clear_cache


def execute():
	if not frappe.db.table_exists("Job Opening"):
		return

	rewritten = 0
	for row in frappe.get_all("Job Opening", fields=["name", "route"]):
		if not row.route or not row.route.startswith("jobs/"):
			continue
		try:
			doc = frappe.get_doc("Job Opening", row.name)
			doc.route = None
			doc.save(ignore_permissions=True)
			rewritten += 1
		except Exception:
			# JobOpening.validate re-runs every HRMS check, and
			# validate_current_vacancies throws when an opening outgrew its
			# staffing plan. One stale opening must not abort `bench migrate`
			# -- it keeps its old route and the /jobs redirect still carries
			# visitors to the right place.
			frappe.log_error(
				title="Job Opening route rewrite failed",
				message=f"{row.name}: {frappe.get_traceback()}",
			)

	if rewritten:
		# _find_matching_document_webview is @redis_cache(ttl=3600); only
		# clear_routing_cache() flushes it, and doc.save() only does that for
		# the doc it touched.
		clear_cache()
