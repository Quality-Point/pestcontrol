# Copyright (c) 2026, QualityPoint and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from pestcontrol.pc_website.utils import validate_articles


class WebsiteGalleryItem(Document):
	def validate(self):
		validate_articles(self)

	def before_save(self):
		# set the title field from the first row title field in content child table
		if self.article and self.article[0].title:
			self.title = self.article[0].title
