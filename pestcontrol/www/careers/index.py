import frappe
from frappe import _

from pestcontrol.pc_website.utils import get_website_context

# Listed in /sitemap.xml. frappe's www sitemap only includes pages that
# opt in with this module attribute (website/router.py load_properties_from_controller).
sitemap = 1


def get_context(context):
	get_website_context(context)
	context.no_cache = 1
	context.title = _("Careers")
	context.description = _(
		"Join the Skystar team. Current openings for technicians, supervisors and office staff in pest control and environmental services."
	)
	context.page_h1 = _("Careers")
	context.breadcrumbs = [
		{"label": _("home"), "route": ""},
		{"label": _("careers"), "route": "careers"},
	]

	# Straight from HRMS Job Openings -- admins create them there, tick
	# "Publish on website" and set Status = Open. Same filter HRMS's own
	# /jobs portal uses. `route` comes from PCJobOpening, so every card links
	# into the careers section rather than HRMS's jobs/<company>/ tree.
	context.job_openings = frappe.get_all(
		"Job Opening",
		filters={"status": "Open", "publish": 1},
		fields=[
			"name",
			"job_title",
			"route",
			"location",
			"department",
			"employment_type",
			"closes_on",
		],
		order_by="posted_on desc",
	)

	# Filter options are derived from what is actually open, not from the
	# Department and Branch masters: offering a filter that matches nothing
	# is worse than offering no filter.
	context.departments = sorted({j.department for j in context.job_openings if j.department})
	context.locations = sorted({j.location for j in context.job_openings if j.location})
