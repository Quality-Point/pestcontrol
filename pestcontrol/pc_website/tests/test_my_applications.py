# Copyright (c) 2026, QualityPoint and contributors
# For license information, please see license.txt

"""Tests for the applicant's own view of their applications.

The scoping tests carry the weight. `get_my_applications` reads through
frappe.get_all, which is get_list(ignore_permissions=True) -- the `owner`
filter is the only thing standing between one applicant and everybody else's
phone numbers and cover letters. A regression there is a data leak, not a
rendering bug, so it is asserted from both directions: that a user sees their
own, and that they do not see anyone else's.

The other half guards decision that the raw HRMS status never reaches the
browser: "Rejected" and "Hold" must both arrive as the "closed" stage.
"""

import frappe
from frappe.tests.utils import FrappeTestCase

from pestcontrol.pc_website.applications import (
	APPLICANT_STAGES,
	DEFAULT_STAGE,
	get_my_applications,
	get_my_applications_json,
	stage_for,
)
from pestcontrol.pc_website.tests.test_job_opening_routes import _designation, _opening

USER_A = "_test_applicant_a@example.com"
USER_B = "_test_applicant_b@example.com"
# Applied without signing in: owner is "Guest", so it must stay unreachable.
GUEST_EMAIL = "_test_applicant_guest@example.com"


def _website_user(email):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"user_type": "Website User",
				# No outgoing Email Account on this site; frappe would throw
				# trying to send the welcome mail.
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
	return email


def _apply_as(user, job_opening=None, status="Open", email=None):
	"""Insert a Job Applicant owned by `user`.

	insert() stamps `owner` from the session, so the session is what has to
	be switched -- there is no field to set. Job Applicant.autoname makes the
	docname the email, hence the namespaced addresses.

	`email` is separate from `user` because that is exactly the case being
	tested: a guest application has owner "Guest" but a real address in
	email_id, and "Guest" itself would fail validate_email_address().
	"""
	email = email or user
	frappe.set_user(user)
	try:
		doc = frappe.get_doc(
			{
				"doctype": "Job Applicant",
				"applicant_name": email.split("@")[0],
				"email_id": email,
				"status": status,
				"job_title": job_opening,
			}
		).insert(ignore_permissions=True)
	finally:
		frappe.set_user("Administrator")
	return doc


class TestMyApplications(FrappeTestCase):
	def setUp(self):
		# A leaked session user poisons every later test in the run, so this
		# is unconditional rather than only on the paths that switch user.
		self.addCleanup(frappe.set_user, "Administrator")

	def _delete_later(self, doctype, name):
		"""Register a teardown delete that restores Administrator first.

		addCleanup runs LIFO, so a set_user("Administrator") registered in
		setUp runs *after* every delete registered later -- leaving the
		deletes to execute as a Website User, which has no delete permission
		on Job Applicant. Resetting inside the cleanup makes the order
		irrelevant.
		"""

		def _delete():
			frappe.set_user("Administrator")
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)

		self.addCleanup(_delete)

	# -- scoping ----------------------------------------------------------

	def test_user_sees_only_own_applications(self):
		"""The one that matters: the owner filter is the whole permission
		model for these rows."""
		a = _apply_as(_website_user(USER_A))
		b = _apply_as(_website_user(USER_B))
		self._delete_later("Job Applicant", b.name)
		self._delete_later("Job Applicant", a.name)

		frappe.set_user(USER_A)
		names = [row["name"] for row in get_my_applications()]
		self.assertIn(a.name, names)
		self.assertNotIn(b.name, names)

	def test_guest_sees_nothing(self):
		"""Without the Guest short-circuit, {"owner": "Guest"} returns every
		anonymous application on the site."""
		guest_application = _apply_as("Guest", email=GUEST_EMAIL)
		self._delete_later("Job Applicant", guest_application.name)

		frappe.set_user("Guest")
		self.assertEqual(get_my_applications(), [])
		self.assertEqual(get_my_applications_json(), "")

	# -- the raw status must not cross the wire ---------------------------

	def test_payload_never_contains_raw_status(self):
		user = _website_user(USER_A)
		for status in APPLICANT_STAGES:
			doc = _apply_as(user, status=status)
			try:
				frappe.set_user(user)
				payload = get_my_applications_json()
				frappe.set_user("Administrator")
				self.assertNotIn("Rejected", payload, f"raw status leaked for {status}")
				self.assertNotIn('"status"', payload, f"status key present for {status}")
			finally:
				frappe.set_user("Administrator")
				frappe.delete_doc("Job Applicant", doc.name, force=True, ignore_permissions=True)

	def test_every_status_option_has_a_stage(self):
		"""Read the options off the doctype, so an HRMS release that adds a
		status fails here rather than silently falling back."""
		options = frappe.get_meta("Job Applicant").get_field("status").options.split("\n")
		for status in filter(None, options):
			self.assertIn(status, APPLICANT_STAGES, f"{status} has no applicant-facing stage")

	def test_rejected_and_hold_collapse_to_closed(self):
		self.assertEqual(stage_for("Rejected"), "closed")
		self.assertEqual(stage_for("Hold"), "closed")

	def test_unknown_status_falls_back(self):
		self.assertEqual(stage_for("Some Future Status"), DEFAULT_STAGE)

	# -- payload shape ----------------------------------------------------

	def test_general_application_has_no_job(self):
		"""job_title is None whenever the form was submitted without a live
		opening -- the endpoint drops one that is not Open."""
		user = _website_user(USER_A)
		doc = _apply_as(user)
		self._delete_later("Job Applicant", doc.name)

		frappe.set_user(user)
		row = next(r for r in get_my_applications() if r["name"] == doc.name)
		self.assertIsNone(row["job_url"])
		self.assertTrue(row["title"])

	def test_open_published_opening_is_linked(self):
		opening = _opening("Zzz Portal Linked Role", publish=1)
		opening.insert(ignore_permissions=True)
		user = _website_user(USER_A)
		doc = _apply_as(user, job_opening=opening.name)
		self._delete_later("Job Opening", opening.name)
		self._delete_later("Job Applicant", doc.name)

		frappe.set_user(user)
		row = next(r for r in get_my_applications() if r["name"] == doc.name)
		self.assertEqual(row["title"], "Zzz Portal Linked Role")
		self.assertTrue(row["job_url"].endswith(opening.route))

	def test_unpublished_opening_has_no_link(self):
		"""An unpublished route 404s, so the title renders as plain text."""
		opening = _opening("Zzz Portal Unpublished Role", publish=0)
		opening.insert(ignore_permissions=True)
		user = _website_user(USER_A)
		doc = _apply_as(user, job_opening=opening.name)
		self._delete_later("Job Opening", opening.name)
		self._delete_later("Job Applicant", doc.name)

		frappe.set_user(user)
		row = next(r for r in get_my_applications() if r["name"] == doc.name)
		self.assertIsNone(row["job_url"])

	def test_deleted_opening_falls_back_to_designation(self):
		"""designation has fetch_from job_title.designation, which frappe
		resolves server-side before insert -- so the value is on the row and
		outlives a force-deleted opening."""
		opening = _opening("Zzz Portal Doomed Role", publish=1)
		opening.insert(ignore_permissions=True)
		user = _website_user(USER_A)
		doc = _apply_as(user, job_opening=opening.name)
		self._delete_later("Job Applicant", doc.name)
		frappe.delete_doc("Job Opening", opening.name, force=True)

		frappe.set_user(user)
		row = next(r for r in get_my_applications() if r["name"] == doc.name)
		self.assertEqual(row["title"], _designation())
		self.assertIsNone(row["job_url"])
