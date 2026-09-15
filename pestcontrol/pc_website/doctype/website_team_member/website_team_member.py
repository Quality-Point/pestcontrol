# Copyright (c) 2026, QualityPoint and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.website.website_generator import WebsiteGenerator

from pestcontrol.pc_website.utils import (
	attach_articles,
	get_website_context,
	validate_articles,
)


class WebsiteTeamMember(WebsiteGenerator):
	website = frappe._dict(template="pestcontrol/templates/generators/website_team_member.html")

	def validate(self):
		validate_articles(self)
		if not self.route:
			# self.scrub() is frappe's cleanup_page_name: Unicode-safe, so a
			# non-Latin title slugs to itself instead of to an empty string.
			if self.member_name:
				self.route = f"team/{self.scrub(self.member_name)}"
		super().validate()

	def get_context(self, context):
		get_website_context(context)
		context.no_cache = 1
		attach_articles("Website Team Member", [self])
		context.title = self.member_name
		context.page_h1 = context.title
		context.page_header_image = self.header_image
		context.breadcrumbs = [
			{"label": _("home"), "route": ""},
			{"label": _("team"), "route": "team"},
			{"label": context.page_h1, "route": self.route},
		]

	def before_save(self):
		# set the title field from the first row title field in content child table
		if self.article and self.article[0].title:
			self.title = self.article[0].title
