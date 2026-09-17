# Copyright (c) 2026, QualityPoint and contributors
# For license information, please see license.txt

"""The applicant's own view of what they sent through the careers form.

HRMS `Job Applicant` is desk-only -- no web view, no route, and no field
linking it to a User -- so there is no read path an applicant could ever
reach. This builds one, for the portal, under two constraints:

  * **Scoped by `owner`, never by email.** `Document.insert()` stamps
    `owner = frappe.session.user`, so an application submitted while signed
    in already belongs to that account with no extra field and no backfill.
    Email would be the obvious key -- Job Applicant.autoname even makes the
    docname the email -- but `require_email_verification` can be off, and is
    off here, so anyone could register with someone else's address and read
    their application. `owner` cannot be claimed that way.

  * **The raw status never leaves the server.** HR's `Rejected` and `Hold`
    both surface as "Closed". Mapping this client-side would put the real
    word in view-source no matter what the page rendered.

Guest applications have `owner = "Guest"` and are deliberately unreachable.
"""

import frappe
from frappe import _

from pestcontrol.pc_website.utils import get_site_languages

# HRMS status -> what the applicant is told. Two statuses collapse into
# `closed`: an applicant should learn they were rejected from a person, not
# from a chip on a dashboard.
APPLICANT_STAGES = {
	"Open": "received",
	"Replied": "under_review",
	"Shortlisted": "shortlisted",
	"Hold": "closed",
	"Rejected": "closed",
	"Accepted": "accepted",
}

# Anything HRMS adds in a future release lands here rather than leaking a
# status this site has never seen. test_every_status_option_has_a_stage reads
# the doctype's own options so that upgrade fails loudly instead.
DEFAULT_STAGE = "received"

MAX_APPLICATIONS = 50


def stage_for(status):
	return APPLICANT_STAGES.get(status, DEFAULT_STAGE)


def stage_label(stage):
	"""Translated label for a stage.

	Built inside the function rather than as a module-level dict: a bench
	worker serves every site out of the same process, and `_()` resolves
	against whichever site is active on the current request. A dict built at
	import time would bake in whichever site happened to import this module
	first; building it fresh here means each call resolves under its own
	request's language.
	"""
	labels = {
		"received": _("Received"),
		"under_review": _("Under review"),
		"shortlisted": _("Shortlisted"),
		"closed": _("Closed"),
		"accepted": _("Accepted"),
	}
	return labels.get(stage, labels[DEFAULT_STAGE])


def get_my_applications():
	"""The signed-in user's own applications, newest first.

	Returns plain dicts safe to hand to the browser: no `status`, no
	`applicant_rating`, no `notes`.
	"""
	user = frappe.session.user
	# frappe.get_all is get_list(ignore_permissions=True), so the `owner`
	# filter below is the only thing protecting these rows. Without this
	# guard, {"owner": "Guest"} returns every guest application on the site.
	if not user or user == "Guest":
		return []

	rows = frappe.get_all(
		"Job Applicant",
		filters={"owner": user},
		fields=["name", "status", "job_title", "designation", "creation"],
		order_by="creation desc",
		limit_page_length=MAX_APPLICATIONS,
	)
	if not rows:
		return []

	openings = _openings_for(rows)
	return [_application(row, openings.get(row.job_title)) for row in rows]


def get_my_applications_json():
	"""Serialized for embedding in a <script type="application/json"> block.

	Frappe never enables jinja autoescaping, so this is injected raw into the
	page. `job_title` is HR-supplied free text, and a literal `</script>` in
	it would break out of the block; `\\u003c` is valid JSON that JSON.parse
	turns back into `<`.
	"""
	applications = get_my_applications()
	if not applications:
		return ""
	return frappe.as_json(applications).replace("<", "\\u003c")


def _openings_for(rows):
	"""One query for every linked opening, keyed by name."""
	names = {row.job_title for row in rows if row.job_title}
	if not names:
		return {}
	return {
		opening.name: opening
		for opening in frappe.get_all(
			"Job Opening",
			filters={"name": ("in", list(names))},
			fields=["name", "job_title", "route", "status", "publish"],
		)
	}


def _application(row, opening):
	return {
		"name": row.name,
		"title": _title(row, opening),
		# isoformat, not the raw datetime: frappe's json_handler emits
		# "YYYY-MM-DD HH:mm:ss.ffffff", which javascript's Date does not
		# parse reliably.
		"applied_on": row.creation.isoformat() if row.creation else None,
		"stage": stage_for(row.status),
		"stage_label": stage_label(stage_for(row.status)),
		"job_url": _job_url(opening),
	}


def _title(row, opening):
	"""The role applied for, degrading as the data thins out.

	`designation` is not a fallback of last resort -- it has
	`fetch_from: job_title.designation`, which frappe resolves server-side
	before insert, so the value is stored on the row and outlives the opening
	even if someone force-deletes it.
	"""
	if opening and opening.job_title:
		return opening.job_title
	return row.designation or _("General application")


def _job_url(opening):
	"""Link to the opening only while it is a live, public page.

	An unpublished route 404s and a closed one is a dead end. Returning None
	for a closed opening also keeps pipeline state off the page -- "this job
	is closed" tells the applicant something HR has not told them.
	"""
	if not opening or not opening.route:
		return None
	if not opening.publish or opening.status != "Open":
		return None
	return f"/{_lang_prefix()}/{opening.route}"


def _lang_prefix():
	"""Language segment for a link built off the portal.

	Not `u()`: that reads frappe.local.pc_prefix, which is empty on /portal
	because the portal is served without a language prefix, so it would fall
	back to the site's configured default and send an arabic reader to the
	english job page. The portal's own active language is the right answer.
	"""
	languages = {row["code"] for row in get_site_languages()}
	lang = frappe.local.lang
	return lang if lang in languages else "en"
