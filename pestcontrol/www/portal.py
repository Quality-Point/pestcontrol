from frappe.sessions import get_csrf_token

from pestcontrol.pc_website.utils import portal_user_info

# This file exists because frappe resolves a www page's python controller from
# the SAME app the matching .html was found in (TemplatePage.set_pymodule), so
# overriding portal.html without a portal.py leaves the page with no context at
# all.
#
# It used to delegate to frappe.www.portal.get_context, but that module does
# not exist in frappe v15 -- the import alone raised ModuleNotFoundError, which
# 500'd /portal and, because get_pages() imports every www controller, also
# broke /sitemap.xml and anything else that enumerates website pages.
#
# portal.html needs `me` (full_name/email/user_image) and a csrf token; the
# optional `doctype`/`raw_result` vars are only set on the list routes
# (/orders, /quotations, /invoices), which frappe serves through ListPage and
# never reach this controller.
no_cache = 1


def get_context(context, **dict_params):
	context.me = portal_user_info()
	context.csrf_token = get_csrf_token()
	return context
