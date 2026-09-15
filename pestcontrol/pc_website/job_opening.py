# Copyright (c) 2026, QualityPoint and contributors
# For license information, please see license.txt

"""Skystar's public face for HRMS `Job Opening`.

Registered as `override_doctype_class`, which is the only way to reach two
things HRMS hard-codes on the class itself:

  * `website.template`. HRMS points at the bare path
    "templates/generators/job_opening.html". Bare paths resolve through the
    jinja ChoiceLoader against reversed(installed_apps), and hrms installs
    after pestcontrol -- so a file dropped at
    pestcontrol/templates/generators/job_opening.html would be shadowed
    forever. The app-prefixed path below goes through the PrefixLoader
    instead, which is exact and immune to install order.

  * The route. HRMS builds `jobs/<company>/<job-title>`; the careers section
    owns these pages, so they belong under `careers/<job-title>`.

Nothing in apps/hrms is modified. This subclasses JobOpening and delegates,
so every HRMS validation still runs.

HRMS's per-opening `job_application_route` (an override for where the Apply
button points) is deliberately ignored: the site has one apply flow, through
one rate-limited endpoint. Honouring it again would be one `{% if %}` in the
template.
"""

import frappe
from frappe import _
from frappe.utils import format_date, strip_html
from hrms.hr.doctype.job_opening.job_opening import JobOpening

from pestcontrol.pc_website.utils import get_website_context

ROUTE_PREFIX = "careers"

# Slugs that would shadow a real page. `/careers/apply` is a www page, but
# frappe's PathResolver tries DocumentPage *before* TemplatePage, so a
# published opening routed at `careers/apply` would win and the application
# form would become unreachable. Add a string here whenever a new page is
# added under www/careers/.
RESERVED_SLUGS = frozenset(("apply", "index"))

# frappe's own cap, applied by WebsiteGenerator.set_route -- which never runs
# here, because HRMS's validate() does not call super().
MAX_ROUTE_LENGTH = 139

# Job Opening.route carries a unique index, so a collision is a
# DuplicateEntryError at insert rather than a message anyone can act on.
MAX_SLUG_ATTEMPTS = 50


class PCJobOpening(JobOpening):
	website = frappe._dict(
		template="pestcontrol/templates/generators/job_opening.html",
		condition_field="publish",
		page_title_field="job_title",
	)

	def validate(self):
		# HRMS only builds a route when the field is empty, so setting it
		# first wins without patching anything. `if not self.route` is its
		# rule as much as ours: a live URL must not move when someone fixes a
		# typo in the job title.
		if not self.route:
			self.route = self._careers_route()
		super().validate()

	def _careers_route(self):
		"""`careers/<slug>`, unique and safe to serve.

		Does the hygiene WebsiteGenerator.set_route would normally apply.
		HRMS's validate() never calls super(), so none of it happens
		otherwise -- neither the length cap nor the `/.` stripping.
		"""
		slug = self.scrub(self.job_title or "")
		# cleanup_page_name returns "" for a title that is only punctuation.
		# That would make the route bare `careers` and shadow the listing.
		if not slug or slug in RESERVED_SLUGS:
			slug = self.scrub(self.name or "") or "opening"

		slug = slug[: MAX_ROUTE_LENGTH - len(ROUTE_PREFIX) - 1]
		return self._unique_route(slug)

	def _unique_route(self, slug):
		candidate = f"{ROUTE_PREFIX}/{slug}".strip("/.")
		for attempt in range(2, MAX_SLUG_ATTEMPTS + 2):
			if not frappe.db.exists("Job Opening", {"route": candidate, "name": ("!=", self.name)}):
				return candidate
			candidate = f"{ROUTE_PREFIX}/{slug}-{attempt}".strip("/.")
		# Two branches hiring for the same title is ordinary; fifty is not.
		return f"{ROUTE_PREFIX}/{self.scrub(self.name or '')}".strip("/.")

	def get_context(self, context):
		# Deliberately not calling super(): HRMS's get_context sets
		# `context.parents`, which drives frappe's own breadcrumb template.
		# This theme renders context.breadcrumbs through page_header.html.
		get_website_context(context)
		context.no_cache = 1

		context.title = self.job_title
		context.page_h1 = self.job_title
		context.description = strip_html(self.description or "")[:155].strip() or _(
			"Job opening at Skystar."
		)
		context.breadcrumbs = [
			{"label": _("home"), "route": ""},
			{"label": _("careers"), "route": ROUTE_PREFIX},
			{"label": self.job_title, "route": self.route},
		]

		context.is_open = self.status == "Open"
		context.apply_url = f"/{ROUTE_PREFIX}/apply"
		context.department_label = self.department
		context.location_label = self.location
		context.employment_type = self.employment_type
		context.salary_display = self.salary_display()
		context.no_of_applications = (
			frappe.db.count("Job Applicant", {"job_title": self.name})
			if self.publish_applications_received
			else None
		)
		# format_date is babel-localised; HRMS's own template uses pretty_date
		# ("3 days ago"), which has no arabic form and renders as english text
		# in the middle of an arabic page.
		context.posted_on_display = format_date(self.posted_on, "d MMM, YYYY") if self.posted_on else None
		context.closes_on_display = format_date(self.closes_on, "d MMM, YYYY") if self.closes_on else None

		# A closed opening keeps its URL -- someone following a shared link
		# deserves "this role is closed" over a 404 -- but must not stay in
		# the index once it is no longer fillable. seo.py honours this.
		if not context.is_open:
			context.seo_noindex = True

	def salary_display(self):
		"""Formatted pay range, or None when HR has not published one.

		Built here rather than in the template: every other pestcontrol page
		hands jinja finished strings, and a `frappe.format_value` call buried
		in markup cannot be tested.
		"""
		if not self.publish_salary_range:
			return None
		if not (self.lower_range or self.upper_range):
			return None

		bounds = [
			# _dict, not a plain dict: format_value only coerces a *string* df,
			# and every branch below it uses attribute access.
			frappe.format_value(
				bound, frappe._dict(fieldtype="Currency", options="currency"), self
			)
			for bound in (self.lower_range, self.upper_range)
			if bound
		]
		amount = " - ".join(bounds)
		return f"{amount} / {_(self.salary_per)}" if self.salary_per else amount
