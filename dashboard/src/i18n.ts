export type Lang = 'en' | 'ar';

// Scope note: only the dashboard's own static UI chrome lives here (nav
// labels, headings, button text, empty states). Record data — Quotation/
// Order numbers, ERPNext status values, item names, dates — comes straight
// from the backend and is intentionally left as-is, matching how the rest
// of the site draws the line between translated site chrome and untouched
// record data (see pestcontrol.pc_website.utils.localize for that system).
const strings = {
	en: {
		appTitle: 'My Dashboard',
		navOverview: 'Overview',
		navOrders: 'Orders',
		navQuotations: 'Quotations',
		navInvoices: 'Invoices',
		navMyJobs: 'My Jobs',
		navAccount: 'My Account',
		homeTooltip: 'Back to site',
		accountTooltip: 'My Account',
		welcomeBack: 'Welcome back',
		statusBreakdown: 'Status breakdown',
		noStatusDataYet:
			'Nothing to show yet — once you have orders, quotations, or invoices, their status breakdown will appear here.',
		noItemsYet: (title: string) => `No ${title.toLowerCase()} yet.`,
		back: 'Back',
		print: 'Print',
		grandTotal: 'Grand Total',
		myAccountTitle: 'My Account',
		editProfile: 'Edit Profile',
		resetPassword: 'Reset Password',
		logout: 'Logout',
		// Only the row label — the stage itself ("Received", "Under review",
		// ...) is computed and translated server-side in
		// pc_website/applications.py, so it arrives ready to render — the raw
		// HRMS status deliberately never reaches the browser.
		appliedOn: 'Applied',
		noApplicationsYet: "You haven't applied to any jobs yet."
	},
	ar: {
		appTitle: 'لوحتي',
		navOverview: 'نظرة عامة',
		navOrders: 'الطلبات',
		navQuotations: 'عروض الأسعار',
		navInvoices: 'الفواتير',
		navMyJobs: 'وظائفي',
		navAccount: 'حسابي',
		homeTooltip: 'العودة للموقع',
		accountTooltip: 'حسابي',
		welcomeBack: 'مرحباً بعودتك',
		statusBreakdown: 'توزيع الحالات',
		noStatusDataYet: 'لا يوجد شيء لعرضه بعد — بمجرد أن يكون لديك طلبات أو عروض أسعار أو فواتير، سيظهر توزيع حالتها هنا.',
		noItemsYet: (title: string) => `لا توجد ${title} حتى الآن.`,
		back: 'رجوع',
		print: 'طباعة',
		grandTotal: 'الإجمالي الكلي',
		myAccountTitle: 'حسابي',
		editProfile: 'تعديل الملف الشخصي',
		resetPassword: 'إعادة تعيين كلمة المرور',
		logout: 'تسجيل الخروج',
		appliedOn: 'تم التقديم',
		noApplicationsYet: 'لم تتقدم لأي وظيفة بعد.'
	}
} as const;

export function t(lang: Lang | undefined) {
	return strings[lang === 'ar' ? 'ar' : 'en'];
}
