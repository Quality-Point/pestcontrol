# Copyright (c) 2026, QualityPoint and contributors
# For license information, please see license.txt

"""Tests for PCJobOpening -- the careers section's view of HRMS Job Opening.

Route building carries most of the risk here. `Job Opening.route` has a real
unique index, so a collision is a DuplicateEntryError on insert rather than a
message anyone can act on; and `careers/apply` is a www page that a published
opening would shadow outright, because frappe's PathResolver tries
DocumentPage before TemplatePage.

HRMS's own validate() never calls super(), so none of WebsiteGenerator's route
hygiene runs -- the length cap in particular is ours to apply and ours to
regress.
"""

import frappe
from frappe.tests.utils import FrappeTestCase

from pestcontrol.pc_website.api import _read_resume
from pestcontrol.pc_website.job_opening import MAX_ROUTE_LENGTH

TEST_DESIGNATION = "_Test Careers Designation"


def _designation():
	"""HRMS's validate_current_vacancies passes `designation` straight into
	get_active_staffing_plan_details, which is type-annotated `str` -- so a
	Job Opening without one cannot be validated at all."""
	if not frappe.db.exists("Designation", TEST_DESIGNATION):
		frappe.get_doc({"doctype": "Designation", "designation_name": TEST_DESIGNATION}).insert(
			ignore_permissions=True
		)
	return TEST_DESIGNATION


def _opening(job_title, **kwargs):
	"""An unsaved Job Opening. Most cases call _careers_route() directly, so
	they never touch the database; the two that do need a real designation."""
	doc = frappe.new_doc("Job Opening")
	doc.job_title = job_title
	doc.company = frappe.defaults.get_global_default("company")
	doc.designation = _designation()
	doc.status = "Open"
	doc.update(kwargs)
	return doc


class TestJobOpeningRoutes(FrappeTestCase):
	def test_route_lives_under_careers(self):
		# A title no real opening uses: _careers_route() checks the live table
		# for collisions, so a realistic title makes this assert the site's
		# data rather than the slug rule.
		doc = _opening("Zzz Verification Role")
		self.assertEqual(doc._careers_route(), "careers/zzz-verification-role")

	def test_route_slug_is_unicode_safe(self):
		"""cleanup_page_name keeps arabic; it must not slug to an empty string
		and fall back to the docname."""
		doc = _opening("فني مكافحة آفات")
		route = doc._careers_route()
		self.assertTrue(route.startswith("careers/"))
		self.assertIn("مكافحة", route)

	def test_punctuation_only_title_does_not_shadow_the_listing(self):
		"""A bare `careers` route would take over the listing page itself."""
		doc = _opening("...")
		doc.name = "HR-OPN-2026-9999"
		self.assertNotEqual(doc._careers_route(), "careers")
		self.assertEqual(doc._careers_route(), "careers/hr-opn-2026-9999")

	def test_apply_is_reserved(self):
		"""`careers/apply` is a www page, and DocumentPage resolves first."""
		doc = _opening("Apply")
		doc.name = "HR-OPN-2026-9998"
		self.assertNotEqual(doc._careers_route(), "careers/apply")

	def test_route_is_truncated(self):
		doc = _opening("Zzz " * 60 + "Verification Role")
		self.assertLessEqual(len(doc._careers_route()), MAX_ROUTE_LENGTH)

	def test_existing_route_is_never_rebuilt(self):
		"""A live URL must survive a job-title edit, or every share and every
		indexed result breaks on a typo fix."""
		doc = _opening("Pest Control Technician", route="careers/original-slug")
		doc.validate()
		self.assertEqual(doc.route, "careers/original-slug")

	def test_colliding_titles_get_distinct_routes(self):
		"""HRMS's scheme includes the company; ours does not, so two branches
		hiring the same role collide where HRMS would not."""
		first = _opening("Duplicate Role Title")
		first.insert(ignore_permissions=True)
		self.addCleanup(frappe.delete_doc, "Job Opening", first.name, force=True)

		second = _opening("Duplicate Role Title")
		self.assertNotEqual(second._careers_route(), first.route)
		self.assertTrue(second._careers_route().startswith("careers/duplicate-role-title"))


class TestResumeValidation(FrappeTestCase):
	class _Upload:
		def __init__(self, filename, content):
			self.filename = filename
			self._content = content

		def read(self):
			return self._content

	def test_no_attachment_is_allowed(self):
		"""The resume is optional; a general application need not carry one."""
		self.assertIsNone(_read_resume(None))
		self.assertIsNone(_read_resume(self._Upload("", b"")))

	def test_accepted_extensions_return_bytes(self):
		for name in ("cv.pdf", "CV.PDF", "cv.doc", "cv.docx"):
			self.assertEqual(_read_resume(self._Upload(name, b"data")), b"data")

	def test_rejects_other_extensions(self):
		"""`accept=` on the input is a file-picker hint; a POST can carry
		anything."""
		for name in ("cv.txt", "cv.exe", "cv.pdf.exe", "cv"):
			with self.assertRaises(frappe.ValidationError):
				_read_resume(self._Upload(name, b"data"))

	def test_rejects_empty_file(self):
		with self.assertRaises(frappe.ValidationError):
			_read_resume(self._Upload("cv.pdf", b""))

	def test_rejects_oversized_file(self):
		with self.assertRaises(frappe.ValidationError):
			_read_resume(self._Upload("cv.pdf", b"x" * (5 * 1024 * 1024 + 1)))
