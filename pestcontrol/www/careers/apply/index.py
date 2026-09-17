import frappe
from frappe import _

from pestcontrol.pc_website.utils import get_website_context


def _default_currency():
	company = frappe.defaults.get_global_default("company")
	if company:
		return frappe.get_cached_value("Company", company, "default_currency") or "SAR"
	return "SAR"


# Deliberately NOT in /sitemap.xml: this is a form, and `?job=` would put one
# near-identical variant of it in the index per opening. The openings
# themselves are what should rank.


def get_context(context):
	get_website_context(context)
	context.no_cache = 1
	context.title = _("Apply")
	context.description = _("Apply to join the Skystar team.")
	context.page_h1 = _("Apply")
	context.breadcrumbs = [
		{"label": _("home"), "route": ""},
		{"label": _("careers"), "route": "careers"},
		{"label": _("apply"), "route": "careers/apply"},
	]
	context.seo_noindex = True

	# Reference data for the form's selects. Applications become HRMS Job
	# Applicant records, so these mirror that doctype's country / currency
	# link targets.
	context.countries = frappe.get_all("Country", pluck="name", order_by="name asc")
	context.currencies = frappe.get_all("Currency", filters={"enabled": 1}, pluck="name", order_by="name asc")
	context.default_country = frappe.db.get_default("country") or "Saudi Arabia"
	context.default_currency = _default_currency()

	context.job_opening = None
	context.job_notice = None

	# A stale or shared ?job= link never 404s. Someone who clicked through to
	# apply should land on a form they can still submit, not an error page --
	# so an opening that has closed or been unpublished degrades to the
	# general application with a notice. This mirrors the endpoint, which
	# already drops a non-Open opening and keeps the application.
	requested = frappe.form_dict.get("job")
	if requested:
		row = frappe.db.get_value(
			"Job Opening", requested, ["name", "job_title", "status", "publish", "route"], as_dict=True
		)
		if row and row.status == "Open" and row.publish:
			context.job_opening = row
		else:
			context.job_notice = _(
				"That opening is no longer accepting applications. You can still send us a general application below."
			)
