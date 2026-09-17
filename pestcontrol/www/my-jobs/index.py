import frappe
from frappe import _
from frappe.sessions import get_csrf_token

from pestcontrol.pc_website.applications import get_my_applications_json
from pestcontrol.pc_website.utils import portal_user_info

# Own page rather than a card on /portal (it used to be one, sitting on the
# Overview) -- "Applications" made no sense mixed in with the Orders/
# Quotations/Invoices stat cards, which are unrelated to the careers form.
no_cache = 1


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

	context.me = portal_user_info()
	context.csrf_token = get_csrf_token()
	# Scoped by `owner` inside -- see pc_website/applications.py. Empty string
	# for anyone who has never applied.
	context.applications_json = get_my_applications_json()
	return context
