import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App, { type PageType } from './App';
import type { JobApplication, PortalListRow } from './api/portal';
import type { Lang } from './i18n';

const rootEl = document.getElementById('root');

if (rootEl) {
	const pageType = (rootEl.dataset.pageType as PageType | undefined) ?? 'overview';
	const doctype = rootEl.dataset.doctype;
	const docName = rootEl.dataset.name;
	const printFormat = rootEl.dataset.printFormat;
	const direction = (document.documentElement.getAttribute('dir') as 'ltr' | 'rtl') || 'ltr';
	const lang = (rootEl.dataset.lang as Lang | undefined) ?? 'en';

	const dataEl = document.getElementById('portal-data');
	const embedded = dataEl?.textContent ? JSON.parse(dataEl.textContent) : undefined;

	// Its own block, written only on the Overview by pestcontrol's portal.py.
	// Absent for guests and for anyone who has never applied.
	const applicationsEl = document.getElementById('portal-applications');
	const applications: JobApplication[] = applicationsEl?.textContent
		? JSON.parse(applicationsEl.textContent)
		: [];

	const listRows: PortalListRow[] = pageType === 'list' && Array.isArray(embedded) ? embedded : [];
	const detailDoc: Record<string, unknown> | undefined =
		pageType === 'detail' && embedded && !Array.isArray(embedded) ? embedded : undefined;

	createRoot(rootEl).render(
		<StrictMode>
			<App
				direction={direction}
				lang={lang}
				pageType={pageType}
				doctype={doctype}
				docName={docName}
				printFormat={printFormat}
				listRows={listRows}
				detailDoc={detailDoc}
				applications={applications}
				account={{
					fullName: rootEl.dataset.fullName,
					email: rootEl.dataset.email,
					avatarUrl: rootEl.dataset.avatarUrl
				}}
			/>
		</StrictMode>
	);
}
