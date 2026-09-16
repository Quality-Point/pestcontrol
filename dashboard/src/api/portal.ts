// One row of the signed-in user's own job applications, embedded server-side
// by pestcontrol/www/portal.py. Deliberately carries `stage`/`stage_label`
// and NOT the raw HRMS status: "Rejected" and "Hold" both arrive as the
// "closed" stage, and the real word never reaches the browser.
export interface JobApplication {
	name: string;
	title: string;
	applied_on?: string | null;
	stage: string;
	stage_label: string;
	job_url?: string | null;
}

export interface PortalListRow {
	name: string;
	status?: string;
	transaction_date?: string;
	posting_date?: string;
	grand_total?: number;
	currency?: string;
	[key: string]: unknown;
}

// Used only by the Overview page, which needs a combined view across three
// doctypes that frappe/www/portal.py's get_context() has no equivalent for
// (it only ever computes one doctype's list, driven by the URL). The list
// pages themselves (Orders/Quotations/Invoices) do NOT use this — their
// data is embedded server-side by the portal.html override, avoiding the
// client-fetch param bug (`limit_page_length` vs the real `limit`) that
// caused /dashboard/quotations to silently show nothing.
export async function fetchPortalRows(doctype: string, limit = 100): Promise<PortalListRow[]> {
	const params = new URLSearchParams({ doctype, limit: String(limit) });
	const res = await fetch(`/api/method/frappe.www.list.get_list_data?${params}`, {
		credentials: 'include',
		headers: { Accept: 'application/json' }
	});
	if (!res.ok) return [];
	const body = await res.json();
	// frappe.www.list.get_list_data returns the row list directly as
	// `message` (confirmed via curl) — not wrapped in {raw_result, result}
	// the way frappe/www/portal.py's own get() wraps it for HTML rendering.
	return Array.isArray(body?.message) ? (body.message as PortalListRow[]) : [];
}
