# Copyright (c) 2026, QualityPoint and contributors
# For license information, please see license.txt

"""schema.org JSON-LD for the public website.

Frappe emits no JSON-LD at all -- the only structured data it ships is
breadcrumb microdata -- so the whole graph is ours.

Built in python and serialised with frappe.as_json() rather than assembled in
a template: content here is admin-written arabic prose, and the first time an
editor types a double quote or an ampersand into a meta description, hand-built
JSON in Jinja produces a parse error that silently costs every rich result on
the page.

Everything is emitted as one `@graph` so nodes can reference each other by
`@id` (WebPage -> isPartOf WebSite, Service -> provider Organization). Google's
parser prefers that to a scatter of independent scripts.

A node is only emitted when the data behind it is actually there. An empty
FAQPage or a LocalBusiness with no address is worse than no markup at all: it
publishes a claim about the business that is not true.
"""

import frappe
from frappe.utils import get_url, strip_html

from pestcontrol.pc_website.utils import article_value, localize

# Social profiles, in the order they read best in `sameAs`. Google uses these
# to connect the site to the same entity elsewhere; it is the strongest signal
# available without a Knowledge Panel.
SOCIAL_FIELDS = (
	"google_business_profile_url",
	"instagram_url",
	"facebook_url",
	"twitter_url",
	"linkedin_url",
	"youtube_url",
	"tiktok_url",
	"snapchat_url",
	"linktree_url",
)

# Pages that may carry LocalBusiness. Never site-wide: google flags a business
# location asserted on pages that are not about that location.
LOCAL_BUSINESS_ROUTES = ("branches", "contact")


def build_graph(context):
	"""Return the @graph for a page, or [] when there is nothing to say."""
	settings = context.get("settings")
	if not settings:
		return []

	base = _base(settings)
	nodes = [_organization(settings, base)]

	if webpage := _webpage(context, base):
		nodes.append(webpage)
	if breadcrumb := _breadcrumb(context, base):
		nodes.append(breadcrumb)
	if _is_home(context):
		nodes.append(_website(settings, base))

	doc = context.get("doc")
	if doc:
		nodes.append(_from_document(doc, context, base))

	if _wants_local_business(context):
		nodes.extend(_local_businesses(context, base))

	return [n for n in nodes if n]


# -- entity ---------------------------------------------------------------


def _organization(settings, base):
	node = {
		"@type": "Organization",
		"@id": f"{base}/#organization",
		"name": settings.get("organization_legal_name") or settings.get("site_name"),
		"url": f"{base}/",
	}
	if logo := settings.get("logo"):
		node["logo"] = {"@type": "ImageObject", "url": get_url(logo)}
	# sameAs is the highest-value line in the graph -- it is what ties this
	# site to the same business on google, instagram and the rest.
	if same_as := [settings.get(f) for f in SOCIAL_FIELDS if settings.get(f)]:
		node["sameAs"] = same_as
	if year := settings.get("founding_year"):
		node["foundingDate"] = str(year)
	if identifiers := [v for v in (settings.get("cr_number"), settings.get("vat_number")) if v]:
		node["identifier"] = identifiers
	if contact := _contact_point(settings):
		node["contactPoint"] = contact
	return node


def _contact_point(settings):
	phone = settings.get("phone") or settings.get("whatsapp")
	if not (phone or settings.get("email")):
		return None
	point = {"@type": "ContactPoint", "contactType": "customer service"}
	if phone:
		point["telephone"] = phone
	if email := settings.get("email"):
		point["email"] = email
	point["areaServed"] = settings.get("country") or "SA"
	point["availableLanguage"] = [
		row["code"]
		for row in (frappe.get_all("Language", filters={"enabled": 1}, fields=["name as code"]) or [])
	]
	return point


def _website(settings, base):
	# No SearchAction: this site has no search endpoint, and advertising one
	# that does not exist is an error rather than a missing feature.
	return {
		"@type": "WebSite",
		"@id": f"{base}/#website",
		"url": f"{base}/",
		"name": settings.get("site_name"),
		"inLanguage": frappe.local.lang or "en",
		"publisher": {"@id": f"{base}/#organization"},
	}


# -- per page -------------------------------------------------------------


def _webpage(context, base):
	canonical = context.get("seo_canonical")
	if not canonical:
		return None
	node = {
		"@type": "WebPage",
		"@id": f"{canonical}#webpage",
		"url": canonical,
		"name": context.get("title"),
		"inLanguage": frappe.local.lang or "en",
		"isPartOf": {"@id": f"{base}/#website"},
	}
	if description := (context.get("metatags") or {}).get("description"):
		node["description"] = description
	if image := (context.get("metatags") or {}).get("image"):
		node["primaryImageOfPage"] = {"@type": "ImageObject", "url": image}
	if context.get("breadcrumbs"):
		node["breadcrumb"] = {"@id": f"{canonical}#breadcrumb"}
	return node


def _breadcrumb(context, base):
	"""BreadcrumbList mirroring the visible trail.

	Google requires the markup to match what is on the page, which is why both
	read the one `context.breadcrumbs` list built in each get_context().
	"""
	crumbs = context.get("breadcrumbs")
	canonical = context.get("seo_canonical")
	if not crumbs or not canonical:
		return None
	prefix = getattr(frappe.local, "pc_prefix", "") or ""
	items = []
	for position, crumb in enumerate(crumbs, start=1):
		route = (crumb.get("route") or "").strip("/")
		items.append(
			{
				"@type": "ListItem",
				"position": position,
				"name": crumb.get("label"),
				"item": f"{base}{prefix}/{route}" if route else f"{base}{prefix}/",
			}
		)
	return {"@type": "BreadcrumbList", "@id": f"{canonical}#breadcrumb", "itemListElement": items}


def _from_document(doc, context, base):
	"""The node for a generator page, chosen by doctype."""
	builders = {
		"Website Service": _service,
		"Website Blog Post": _blog_posting,
		"Website Team Member": _person,
		"Job Opening": _job_posting,
	}
	builder = builders.get(doc.get("doctype"))
	return builder(doc, context, base) if builder else None


def _service(doc, context, base):
	node = {
		"@type": "Service",
		"@id": f"{context.seo_canonical}#service",
		"name": localize(doc, "service_name") or context.get("title"),
		"url": context.seo_canonical,
		"provider": {"@id": f"{base}/#organization"},
		"inLanguage": frappe.local.lang or "en",
	}
	if description := localize(doc, "short_description"):
		node["description"] = strip_html(description)
	if image := (doc.get("image") or doc.get("header_image")):
		node["image"] = get_url(image)
	return node


def _blog_posting(doc, context, base):
	node = {
		"@type": "BlogPosting",
		"@id": f"{context.seo_canonical}#post",
		# headline is capped at 110 chars by google; longer is dropped entirely.
		"headline": (localize(doc, "title") or context.get("title") or "")[:110],
		"url": context.seo_canonical,
		"mainEntityOfPage": {"@id": f"{context.seo_canonical}#webpage"},
		"publisher": {"@id": f"{base}/#organization"},
		"inLanguage": frappe.local.lang or "en",
	}
	if intro := localize(doc, "blog_intro"):
		node["description"] = strip_html(intro)
	if image := (doc.get("cover_image") or doc.get("header_image")):
		node["image"] = get_url(image)
	if published := doc.get("published_on"):
		node["datePublished"] = str(published)
	if modified := doc.get("modified"):
		node["dateModified"] = str(modified)
	node["author"] = (
		{"@type": "Person", "name": doc.get("author_name")}
		if doc.get("author_name")
		else {"@id": f"{base}/#organization"}
	)
	return node


def _person(doc, context, base):
	node = {
		"@type": "Person",
		"@id": f"{context.seo_canonical}#person",
		"name": doc.get("member_name"),
		"url": context.seo_canonical,
		"worksFor": {"@id": f"{base}/#organization"},
	}
	if title := localize(doc, "designation"):
		node["jobTitle"] = title
	if photo := doc.get("photo"):
		node["image"] = get_url(photo)
	return node


# -- job openings ---------------------------------------------------------

# Google validates employmentType against a fixed vocabulary; the Employment
# Type doctype is a free-text master, so "Full-time" would be rejected. Keyed
# on the scrubbed value so casing and punctuation in the master do not matter.
# Anything unrecognised is left out rather than guessed at.
EMPLOYMENT_TYPES = {
	"full_time": "FULL_TIME",
	"part_time": "PART_TIME",
	"contract": "CONTRACTOR",
	"contractor": "CONTRACTOR",
	"temporary": "TEMPORARY",
	"intern": "INTERN",
	"internship": "INTERN",
	"apprenticeship": "OTHER",
	"probation": "OTHER",
	"commission": "OTHER",
}

# Job Opening.salary_per is Month/Year; schema.org wants a duration keyword.
SALARY_UNITS = {"month": "MONTH", "year": "YEAR"}


def _job_location(doc, context):
	"""PostalAddress for the opening.

	`location` is a Link to ERPNext's Branch, which holds nothing but a name --
	there is no address behind it. So addressCountry is all that can be stated
	outright, and addressLocality is only added when a published Website Branch
	corroborates the name as a real city. Guessing that "Main Branch" is a
	locality would put a false claim in front of Google, which is exactly what
	this module refuses to do elsewhere.

	Reads context.branches, which get_website_context has already fetched with
	article bundles attached -- the same list _local_businesses works from.
	"""
	address = {"@type": "PostalAddress", "addressCountry": "SA"}
	wanted = (doc.get("location") or "").strip().lower()
	if not wanted:
		return address

	for branch in context.get("branches") or []:
		city = localize(branch, "city")
		if city and city.strip().lower() == wanted:
			address["addressLocality"] = city
			break
	return address


def _job_posting(doc, context, base):
	"""JobPosting for a Job Opening detail page.

	Only the properties google actually reads, and only where the data is
	real. `inLanguage` is the site's default rather than the language being
	served: Job Opening has no Website Article bundle, so the arabic and
	english URLs carry identical english content, and claiming otherwise would
	be a lie the hreflang pair already makes hard enough to defend.
	"""
	node = {
		"@type": "JobPosting",
		"@id": f"{context.seo_canonical}#jobposting",
		"title": doc.get("job_title"),
		"url": context.seo_canonical,
		"hiringOrganization": {"@id": f"{base}/#organization"},
		"inLanguage": frappe.db.get_single_value("PC Website Settings", "default_language") or "en",
		"identifier": {
			"@type": "PropertyValue",
			"name": doc.get("company") or context.settings.get("site_name"),
			"value": doc.get("name"),
		},
		"jobLocation": {"@type": "Place", "address": _job_location(doc, context)},
	}

	if description := doc.get("description"):
		node["description"] = description
	if posted_on := doc.get("posted_on"):
		node["datePosted"] = str(posted_on)
	if closes_on := doc.get("closes_on"):
		node["validThrough"] = str(closes_on)
	if employment_type := EMPLOYMENT_TYPES.get(frappe.scrub(doc.get("employment_type") or "")):
		node["employmentType"] = employment_type

	# Pay is published only when HR ticked the box on the opening; the public
	# page honours that, and so must the markup.
	if doc.get("publish_salary_range") and (doc.get("lower_range") or doc.get("upper_range")):
		value = {"@type": "QuantitativeValue"}
		if doc.get("lower_range"):
			value["minValue"] = doc.get("lower_range")
		if doc.get("upper_range"):
			value["maxValue"] = doc.get("upper_range")
		if unit := SALARY_UNITS.get((doc.get("salary_per") or "").strip().lower()):
			value["unitText"] = unit
		node["baseSalary"] = {
			"@type": "MonetaryAmount",
			"currency": doc.get("currency"),
			"value": value,
		}

	return node


# -- locations ------------------------------------------------------------


def _wants_local_business(context):
	route = (context.get("route") or context.get("path") or "").strip("/")
	return route in LOCAL_BUSINESS_ROUTES or (context.get("doc") or {}).get("doctype") == "Website City"


def _local_businesses(context, base):
	"""One node per branch with enough data to describe a real place.

	The guard is the point, and it deliberately asks for **coordinates** as
	well as city, address and phone.

	LocalBusiness is a factual claim about a physical place, so the bar has to
	separate a finished record from a placeholder -- not merely a full one from
	an empty one. Requiring only "these fields are non-empty" is not enough:
	this site currently carries a test branch whose city, address and phone are
	all filled with keyboard mash, and a presence check happily published it as
	a real location with the phone number 5555555.

	Nothing distinguishes real text from nonsense automatically, so the guard
	uses latitude/longitude as the proxy. Someone looks those up and pastes
	them in deliberately; nobody types them by accident. Coordinates are also
	what makes the node useful -- a LocalBusiness without geo contributes
	little to map and local results anyway.

	Consequence: a branch stays silent until it is genuinely finished, and
	starts appearing the moment it is, with no code change.
	"""
	nodes = []
	for branch in context.get("branches") or []:
		city = localize(branch, "city")
		street = strip_html(localize(branch, "address") or "").strip()
		phone = branch.get("phone")
		if not (city and street and phone):
			continue
		if not (branch.get("latitude") and branch.get("longitude")):
			continue
		node = {
			"@type": ["LocalBusiness", "HomeAndConstructionBusiness"],
			# There is no schema.org type for pest control; productontology
			# wraps the wikipedia article, which is the accepted way to say it.
			"additionalType": "https://www.productontology.org/id/Pest_control",
			"@id": f"{base}/#branch-{frappe.scrub(branch.get('name') or city)}",
			"name": f"{context.settings.get('site_name')} — {city}",
			"telephone": phone,
			"parentOrganization": {"@id": f"{base}/#organization"},
			"address": {
				"@type": "PostalAddress",
				"streetAddress": street,
				"addressLocality": city,
				"addressCountry": "SA",
			},
		}
		if postal := branch.get("postal_code"):
			node["address"]["postalCode"] = postal
		if branch.get("latitude") and branch.get("longitude"):
			node["geo"] = {
				"@type": "GeoCoordinates",
				"latitude": branch.get("latitude"),
				"longitude": branch.get("longitude"),
			}
		if price_range := context.settings.get("price_range"):
			node["priceRange"] = price_range
		if gbp := branch.get("google_business_profile_url"):
			node["sameAs"] = [gbp]
		if hours := _opening_hours(branch):
			node["openingHoursSpecification"] = hours
		nodes.append(node)
	return nodes


def _opening_hours(branch):
	rows = branch.get("opening_hours") or []
	return [
		{
			"@type": "OpeningHoursSpecification",
			"dayOfWeek": row.get("day_of_week"),
			"opens": str(row.get("opens")),
			"closes": str(row.get("closes")),
		}
		for row in rows
		if row.get("day_of_week") and not row.get("is_closed") and row.get("opens")
	]


# -- helpers --------------------------------------------------------------


def _base(settings):
	return (settings.get("canonical_base_url") or get_url()).rstrip("/")


def _is_home(context):
	from frappe.website.utils import get_home_page

	route = (context.get("route") or context.get("path") or "").strip("/")
	return route in ("", get_home_page())
