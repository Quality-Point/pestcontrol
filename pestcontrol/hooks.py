app_name = "pestcontrol"
app_title = "Pest Control"
app_publisher = "QualityPoint"
app_description = "A comprehensive pest control management system built on Frappe, streamlining service scheduling, technician dispatch, chemical inventory tracking, and client reporting"
app_email = "erp@qp.sa"
app_license = "gpl-3.0"

# Apps
# ------------------

required_apps = ["erpnext", "hrms"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "pestcontrol",
# 		"logo": "/assets/pestcontrol/logo.png",
# 		"title": "Pest Control",
# 		"route": "/pestcontrol",
# 		"has_permission": "pestcontrol.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/pestcontrol/css/pestcontrol.css"
app_include_js = "pestcontrol.bundle.js"

# include js, css files in header of web template
web_include_css = "/assets/pestcontrol/website/css/portal.css"
# web_include_js = "/assets/pestcontrol/js/pestcontrol.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "pestcontrol/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "pestcontrol/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
home_page = "home"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
website_generators = [
	"Website Service",
	"Website Project",
	"Website Team Member",
	"Website Blog Post",
	"Website Pest",
]


# Redirects
# ---------

# 301s for routes that have moved. Kept explicit rather than derived: a slug
# only changes when someone renames a record, and the old URL has to keep
# working for whatever already links to it.
website_redirects = [
	# HRMS serves its own unbranded job board at /jobs, and openings used to
	# live at jobs/<company>/<slug>. Both are superseded by the careers
	# section; without these, search engines index two copies of every ad and
	# the stock pages win on nothing but age.
	#
	# resolve_redirect runs *before* the language router, so it never sees a
	# language and cannot add one. The prefixed variants therefore come
	# first, so that an /en/... or /ar/... inbound link -- which is what the
	# router itself emits -- resolves in a single hop. A bare /jobs/... costs
	# two (here, then the router). No target matches any source, so no rule
	# can loop. Patterns are $-anchored by resolve_redirect, so /jobseeker is
	# untouched.
	{"source": r"/(ar|en)/jobs/[^/]+/(.+)", "target": r"/\1/careers/\2"},
	{"source": r"/jobs/[^/]+/(.+)", "target": r"/careers/\1"},
	{"source": r"/(ar|en)/jobs(/.*)?", "target": r"/\1/careers"},
	{"source": r"/jobs(/.*)?", "target": "/careers"},
]

# Fills in the search-engine metadata frappe does not derive on its own --
# canonical, og:url/og:site_name/og:locale, robots -- and lets frappe's own
# MetaTags build the rest from context.title/description/image. Runs after
# each page's get_context(), so it can see context.doc and context.title.
update_website_context = "pestcontrol.pc_website.seo.build_seo_context"

# Serves each language from its own URL (/ar/about, /en/about) so both can be
# indexed; frappe otherwise picks the language by cookie, which a crawler does
# not carry, leaving exactly one language visible to search.
#
# NOTE: this REPLACES frappe's own path resolution for every request, and
# frappe 16 short-circuits only `desk` before the hooks -- /app and /api reach
# it. See pc_website/router.py. Deleting this one line plus `bench clear-cache`
# fully disables it.
website_path_resolver = "pestcontrol.pc_website.router.resolve"

# Document Events
# ---------------

# Frappe never optimises uploads -- optimize_file() exists but nothing calls
# it -- so images attached to website content arrive at whatever resolution
# the camera produced. See pc_website/images.py.
doc_events = {
	"File": {
		"after_insert": "pestcontrol.pc_website.images.optimize_website_upload",
	},
}


# Fixtures
# ----------

# Deliberately does NOT include the website CMS content doctypes (PC
# Website Settings, Website Service, Website Blog Post, etc). They used to
# be listed here so a fresh install wasn't empty, but once the site went
# live, that became actively harmful: `bench migrate` re-imports every
# fixture unconditionally on every run, so any live edit made directly on
# production (a new photo, a service description tweak, an About page
# change...) would get silently overwritten back to whatever the last
# `bench export-fixtures` snapshot in this repo happened to contain the
# next time code was deployed. Production's database is now the sole
# source of truth for all of that content — nothing here pushes into it.
# Only genuinely static, identical-everywhere reference data belongs in
# this list.
# fixtures = [
# 	{"dt": "Language", "filters": [["name", "in", ["en", "ar"]]]},
# ]

# Jinja
# ----------

# add methods and filters to jinja environment
jinja = {
	"methods": [
		"pestcontrol.pc_website.utils.localize",
		"pestcontrol.pc_website.utils.asset_version",
		"pestcontrol.pc_website.utils.doc_to_json",
		"pestcontrol.pc_website.utils.portal_user_info",
		"pestcontrol.pc_website.utils.current_lang",
		"pestcontrol.pc_website.router.u",
		"pestcontrol.pc_website.utils.whatsapp_url",
	],
}

# Installation
# ------------

# before_install = "pestcontrol.install.before_install"
after_install = "pestcontrol.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "pestcontrol.uninstall.before_uninstall"
# after_uninstall = "pestcontrol.uninstall.after_uninstall"

# Site Migration
# --------------

# before_migrate = "pestcontrol.install.before_install"
# after_migrate = "pestcontrol.install.after_install"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "pestcontrol.utils.before_app_install"
# after_app_install = "pestcontrol.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "pestcontrol.utils.before_app_uninstall"
# after_app_uninstall = "pestcontrol.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "pestcontrol.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# Visit Request grants the Customer role a direct DocPerm, which is
# doctype-wide on its own -- every self-registered website user gets that role
# (it is Portal Settings.default_role), so without these three hooks any
# registered visitor can read every customer's visit requests. See
# pc_operation/permissions.py for why all three are needed rather than one.

# Filters lists: the portal, /api/resource/Visit Request, search.
permission_query_conditions = {
	"Visit Request": "pestcontrol.pc_operation.permissions.visit_request_query",
}

# Covers a single document fetched by name, which query conditions never see.
has_permission = {
	"Visit Request": "pestcontrol.pc_operation.permissions.visit_request_has_permission",
}

# Frappe's has_website_permission() returns False when no hook is registered,
# so the portal's own detail view would refuse a customer their own record.
# ERPNext's implementation is generic -- get_customer_field_name() returns
# "customer" for everything that is not a Quotation -- so it fits unchanged.
has_website_permission = {
	"Visit Request": "erpnext.controllers.website_list_for_contact.has_website_permission",
}

# DocType Class
# ---------------
# Override standard doctype classes

# HRMS hard-codes both the website template and the route on the JobOpening
# class itself, and neither is reachable from a hook. `extend_doctype_class`
# (rather than `override_doctype_class`, which frappe's own semgrep rules
# reject: only one app could ever claim it, and it breaks silently if hrms's
# controller class ever moves) mixes PCJobOpening in ahead of hrms's own
# JobOpening in the MRO, so every method PCJobOpening does not define -- every
# HRMS validation -- still resolves to hrms's class untouched. Nothing in
# apps/hrms is modified. See pc_website/job_opening.py.
extend_doctype_class = {
	"Job Opening": "pestcontrol.pc_website.job_opening.PCJobOpening",
}

# Session
# ---------------

# ERPNext's own on_session_creation (create_customer_or_supplier) links a
# self-registered customer's Contact to a Customer but never adds them to
# that Customer's Portal User table — which is what the customer portal
# (and the pestcontrol dashboard) actually filters on. Without this, a
# self-registered customer's own Orders/Quotations/Invoices stay invisible
# to them. See pestcontrol.pc_website.utils.sync_portal_user_on_login.
on_session_creation = "pestcontrol.pc_website.utils.sync_portal_user_on_login"

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"pestcontrol.tasks.all"
# 	],
# 	"daily": [
# 		"pestcontrol.tasks.daily"
# 	],
# 	"hourly": [
# 		"pestcontrol.tasks.hourly"
# 	],
# 	"weekly": [
# 		"pestcontrol.tasks.weekly"
# 	],
# 	"monthly": [
# 		"pestcontrol.tasks.monthly"
# 	],
# }

# Testing
# -------

before_tests = "pestcontrol.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "pestcontrol.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "pestcontrol.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
before_request = ["pestcontrol.pc_website.utils.apply_preferred_language_cookie_on_request"]
# after_request = ["pestcontrol.utils.after_request"]

# Job Events
# ----------
# before_job = ["pestcontrol.utils.before_job"]
# after_job = ["pestcontrol.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"pestcontrol.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
