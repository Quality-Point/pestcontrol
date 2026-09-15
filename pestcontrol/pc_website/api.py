# Copyright (c) 2026, QualityPoint and contributors
# For license information, please see license.txt

import os

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import cint, escape_html, flt, get_url, now_datetime, validate_email_address
from frappe.utils.file_manager import save_file
from frappe.utils.password_strength import test_password_strength
from frappe.utils.verified_command import get_signed_params, verify_request
from frappe.website.utils import is_signup_disabled
from frappe.www.login import sanitize_redirect

# A floor applied to self-registered passwords no matter what
# `System Settings.enable_password_policy` says -- see _validate_password.
# The score is zxcvbn's 0-4 scale; 2 is "somewhat guessable", the same value
# frappe suggests as a default minimum_password_score.
MIN_PASSWORD_LENGTH = 8
MIN_PASSWORD_SCORE = 2

# How long an email-confirmation link stays usable. Frappe's own signed links
# never expire; an account activation is worth bounding.
VERIFICATION_TTL = 24 * 60 * 60

# What a resume may be. `accept=".pdf,.doc,.docx"` on the file input is a
# hint to the file picker and nothing more -- a POST can carry anything.
# save_file would eventually stop an oversized upload via check_max_file_size,
# but only at the site-wide limit and only with frappe's own generic message.
RESUME_EXTENSIONS = frozenset((".pdf", ".doc", ".docx"))
MAX_RESUME_BYTES = 5 * 1024 * 1024


# Reviewed: intentionally public, this is the site's own contact form
# endpoint; no permission check applies since anonymous visitors are
# exactly who's meant to call it.
@frappe.whitelist(allow_guest=True)  # nosemgrep: guest-whitelisted-method
def submit_contact_form(fname: str, lname: str = "", email: str = "", phone: str = "", message: str = ""):
	"""Create a Website Contact Message from the public contact form."""
	full_name = f"{fname} {lname}".strip()
	doc = frappe.get_doc(
		{
			"doctype": "Website Contact Message",
			"full_name": full_name,
			"email": email,
			"phone": phone,
			"message": message,
			"status": "New",
		}
	)
	doc.insert(ignore_permissions=True)
	return {"success": True}


def _read_resume(file_storage):
	"""Validated resume bytes, or None when nothing was attached.

	Runs before the Job Applicant is inserted so a rejected upload produces a
	message about the file rather than frappe's generic size error from
	somewhere downstream. The stream is read once here and the bytes handed
	on -- a FileStorage cannot be read twice."""
	if not file_storage or not file_storage.filename:
		return None

	extension = os.path.splitext(file_storage.filename)[1].lower()
	if extension not in RESUME_EXTENSIONS:
		frappe.throw(_("Please attach your resume as a PDF or Word document."))

	content = file_storage.read()
	if not content:
		frappe.throw(_("The resume you attached is empty."))
	if len(content) > MAX_RESUME_BYTES:
		frappe.throw(_("Your resume is too large. Please attach a file under 5 MB."))

	return content


# Reviewed: intentionally public, this is the site's own job application
# form endpoint; no permission check applies since anonymous applicants are
# exactly who's meant to call it. Rate limited per IP the same way
# register_account is -- a guest endpoint that inserts records and accepts
# uploads is the obvious thing to point a script at. `methods` matters on its
# own: without it a bare GET with query params creates a Job Applicant.
@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
@rate_limit(limit=5, seconds=60 * 60)
def submit_job_application(
	full_name: str,
	email: str,
	phone: str,
	position_applied_for: str = "",
	job_opening: str = "",
	message: str = "",
	country: str = "",
	resume_link: str = "",
	salary_min: str = "",
	salary_max: str = "",
	salary_currency: str = "",
):
	"""Create an HRMS Job Applicant from the public careers form, attaching the
	resume file (if provided) as a private File once the applicant's name exists.

	The careers form's position selector is populated from HRMS Job Openings, so
	it POSTs a `job_opening` id. We link it only if it is still Open — the
	dropdown only lists Open+published openings, but a race could send a
	just-closed one, and Job Applicant.before_insert throws hard on a closed
	opening. When no opening is linked (e.g. the free-text fallback shown when
	there are no open positions), the typed position is preserved in the cover
	letter instead.

	`country` / `salary_currency` are validated against their link targets
	before use so a tampered POST can't inject an arbitrary link value; the
	expected-salary range is optional and only recorded when a positive number
	is given."""
	linked_opening = None
	if job_opening:
		row = frappe.db.get_value("Job Opening", job_opening, ["name", "status"], as_dict=True)
		if row and row.status == "Open":
			linked_opening = row.name

	cover_letter = message or ""
	if not linked_opening and position_applied_for:
		cover_letter = f"{_('Position applied for')}: {position_applied_for}\n\n{cover_letter}".strip()

	lower_range = flt(salary_min)
	upper_range = flt(salary_max)
	has_salary = lower_range > 0 or upper_range > 0
	currency = None
	if has_salary:
		currency = salary_currency if frappe.db.exists("Currency", salary_currency) else None

	doc = frappe.get_doc(
		{
			"doctype": "Job Applicant",
			"applicant_name": full_name,
			"email_id": email,
			"phone_number": phone,
			# Link -> Job Opening; `designation` auto-fetches from it
			"job_title": linked_opening,
			"status": "Open",
			"source": "Website Listing",
			"cover_letter": cover_letter or None,
			"country": country if country and frappe.db.exists("Country", country) else None,
			"resume_link": (resume_link or "").strip() or None,
			"currency": currency,
			"lower_range": lower_range if has_salary else 0,
			"upper_range": upper_range if has_salary else 0,
		}
	)
	resume_file = frappe.request.files.get("resume") if frappe.request else None
	resume_content = _read_resume(resume_file)

	# Job Applicant.before_insert throws on a closed opening, and on a repeat
	# application when the opening has Prevent Duplicate Applications ticked.
	# Both messages are already translated and already meant for the
	# applicant, so they are left to propagate into _server_messages rather
	# than caught and flattened into a generic failure.
	doc.insert(ignore_permissions=True)

	if resume_content is not None:
		file_doc = save_file(
			resume_file.filename,
			resume_content,
			"Job Applicant",
			doc.name,
			is_private=1,
			df="resume_attachment",
		)
		doc.db_set("resume_attachment", file_doc.file_url, update_modified=False)

	return {"success": True}


@frappe.whitelist()
def get_portal_document(doctype: str, name: str):
	"""Read-only JSON pass-through for the customer dashboard's detail view.

	Re-exposes the same check erpnext.templates.pages.order.py already uses
	to gate /orders/<name> etc. — grants nothing new, just makes that
	existing permission decision reachable as JSON instead of a Jinja page.
	"""
	doc = frappe.get_doc(doctype, name)
	if not frappe.has_website_permission(doc):
		frappe.throw(frappe._("Not Permitted"), frappe.PermissionError)
	return doc.as_dict()


# Reviewed: intentionally public, this is the site's own registration
# endpoint; anonymous visitors are exactly who is meant to call it.
@frappe.whitelist(allow_guest=True, methods=["POST"])  # nosemgrep: guest-whitelisted-method
@rate_limit(limit=5, seconds=60 * 60)
def register_account(
	full_name: str, email: str, mobile_no: str, password: str, redirect_to: str = ""
) -> dict:
	"""Create a Website User with a password the visitor chose themselves.

	This exists instead of frappe.core.doctype.user.user.sign_up because that
	one sets `new_password = random_string(10)` and relies on the "Verify Your
	Email" notification to let the user pick their own. This site has no
	outgoing Email Account, so nothing is ever sent: sign_up returns "ask your
	administrator to verify your sign-up" and leaves behind an account that is
	enabled but that nobody can log into -- password reset needs the same
	missing email. Letting the visitor set the password at registration is
	what makes the account usable at all.

	The account is active immediately, with no admin approval, unless
	`PC Website Settings.require_email_verification` is on -- which should stay
	off until a real outgoing Email Account exists, or new accounts go back to
	being locked out.
	"""
	if is_signup_disabled():
		frappe.throw(_("Sign up is disabled"), title=_("Not Allowed"))

	email = (email or "").strip().lower()
	full_name = (full_name or "").strip()
	mobile_no = (mobile_no or "").strip()

	if not (full_name and email and mobile_no and password):
		frappe.throw(_("All fields are required."))

	validate_email_address(email, throw=True)

	if existing := frappe.db.get_value("User", {"email": email}, ["enabled"], as_dict=True):
		# Same wording and shape as frappe's own sign_up, which the login page
		# already leaks this much through anyway.
		return {
			"success": False,
			"message": _("Already Registered") if existing.enabled else _("Registered but disabled"),
		}

	# Same throttle frappe's sign_up applies, for the same reason.
	max_per_hour = cint(frappe.get_system_settings("max_signups_allowed_per_hour") or 300)
	if frappe.db.get_creation_count("User", 60) >= max_per_hour:
		frappe.throw(
			_("Too many accounts were created recently. Please try again in an hour."),
			title=_("Temporarily Disabled"),
		)

	_validate_password(password, [full_name, email, mobile_no])

	require_verification = cint(
		frappe.db.get_single_value("PC Website Settings", "require_email_verification")
	)
	if require_verification and not frappe.db.exists("Email Account", {"enable_outgoing": 1}):
		# Checked before the User is created, not after. Otherwise the account
		# exists, is disabled, and no message is ever sent to enable it --
		# which is precisely the stranded-account bug this endpoint replaces.
		frappe.throw(
			_("Sign up is temporarily unavailable. Please contact us."),
			title=_("Not Available"),
		)

	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": escape_html(full_name),
			"mobile_no": mobile_no,
			"user_type": "Website User",
			# Active without admin approval, which is the whole point; the
			# verification switch is the only thing that holds an account back.
			"enabled": 0 if require_verification else 1,
			"new_password": password,
			# Frappe's welcome email invites the recipient to set a password,
			# which they have just chosen; the verification mail below says the
			# one thing that actually needs saying.
			"send_welcome_email": 0,
		}
	)
	user.flags.ignore_permissions = True
	# Deliberately NOT setting ignore_password_policy: that flag is precisely
	# how sign_up gets away with a random password, and _validate_password
	# above has already applied a floor of its own.
	user.insert()

	# Portal Settings.default_role is "Customer" here, which is what makes
	# erpnext create the Customer + Contact on first session and what every
	# portal scoping rule keys off.
	if default_role := frappe.get_single_value("Portal Settings", "default_role"):
		user.add_roles(default_role)

	if require_verification:
		_send_verification_email(user)
		return {
			"success": True,
			"verify": True,
			"message": _("Please check your email to confirm your account."),
		}

	# Log them straight in: an account they cannot immediately use is the exact
	# failure this endpoint exists to fix. login_manager only exists on a real
	# HTTP request, so a direct call (a test, the console) creates the account
	# and skips the session rather than blowing up.
	if login_manager := getattr(frappe.local, "login_manager", None):
		login_manager.login_as(email)
	return {
		"success": True,
		"verify": False,
		"redirect_to": _safe_redirect(redirect_to),
	}


def _safe_redirect(redirect_to: str) -> str:
	"""Where to send the freshly signed-in visitor.

	sanitize_redirect() compares the target against the *current request's*
	host, so it only works on a real HTTP request. A direct call -- a test, the
	console -- has no request and nowhere to redirect to anyway, so it falls
	back rather than raising. The sanitiser is never skipped when there is a
	request to sanitise against.
	"""
	if redirect_to and getattr(frappe.local, "request", None):
		return sanitize_redirect(redirect_to) or "/portal"
	return "/portal"


def _validate_password(password: str, user_inputs: list) -> None:
	"""Reject a weak password regardless of the site's password policy.

	`System Settings.enable_password_policy` is off on this site, and frappe's
	own strength check short-circuits to a pass when it is -- so without this,
	an account that can read customer records could be created with "123456".
	"""
	if len(password) < MIN_PASSWORD_LENGTH:
		frappe.throw(_("Password must be at least {0} characters long.").format(MIN_PASSWORD_LENGTH))

	result = test_password_strength(password, user_inputs=[i for i in user_inputs if i])
	if cint(result.get("score")) < MIN_PASSWORD_SCORE:
		suggestions = (result.get("feedback") or {}).get("suggestions") or []
		frappe.throw(
			_("Please choose a stronger password.") + ((" " + " ".join(suggestions)) if suggestions else "")
		)


def _send_verification_email(user) -> None:
	"""Mail the one link that can turn a pending account on."""
	params = get_signed_params(
		{"email": user.name, "expires": cint(now_datetime().timestamp()) + VERIFICATION_TTL}
	)
	link = get_url(f"/api/method/pestcontrol.pc_website.api.verify_account?{params}")

	frappe.sendmail(
		recipients=user.name,
		subject=_("Confirm your account"),
		message=_("Hello {0},").format(user.first_name)
		+ "<br><br>"
		+ _("Please confirm your email address to activate your account.")
		+ f'<br><br><a href="{link}">'
		+ _("Confirm my account")
		+ "</a><br><br>"
		+ _("This link expires in {0} hours.").format(VERIFICATION_TTL // 3600),
		now=True,
	)


# Reviewed: intentionally public. The link is HMAC-signed by frappe and
# carries its own expiry, so possession of the URL is the authorisation.
@frappe.whitelist(allow_guest=True, methods=["GET"])  # nosemgrep: guest-whitelisted-method
def verify_account(email: str, expires: str, **kwargs):
	"""Enable an account that was held back for email verification."""
	if not verify_request():
		# verify_request() has already rendered an "Invalid Link" page.
		return

	if cint(expires) < cint(now_datetime().timestamp()):
		frappe.respond_as_web_page(
			_("Link Expired"),
			_("This confirmation link has expired. Please sign up again."),
			indicator_color="red",
		)
		return

	# Only ever flips a *pending* account on, so this can neither re-enable an
	# account an administrator later disabled nor be replayed to any effect.
	if frappe.db.get_value("User", email, "enabled") == 0:
		frappe.db.set_value("User", email, "enabled", 1)
		# Required, not defensive: frappe's sync_database() rolls back any
		# request whose method is "safe", and this link is a GET. Without the
		# commit the account is enabled for the length of the request and then
		# quietly reverted -- the link would look like it worked.
		frappe.db.commit()  # nosemgrep: frappe-manual-commit

	frappe.local.flags.redirect_location = "/account/login?verified=1"
	raise frappe.Redirect
