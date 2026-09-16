import { useEffect, useMemo, useState } from 'react';
import { Box, Card, CardContent, Typography, Grid, Skeleton, Divider, Link, Stack } from '@mui/material';
import { PieChart } from '@mui/x-charts/PieChart';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import RequestQuoteIcon from '@mui/icons-material/RequestQuote';
import DescriptionIcon from '@mui/icons-material/Description';
import { fetchPortalRows, type JobApplication, type PortalListRow } from '../api/portal';
import StatusChip, { type ChipColor } from '../components/StatusChip';
import { t, type Lang } from '../i18n';

// Keyed on the stable `stage` the server sends, never on the label — the
// label is already translated, so an english-keyed map would fall through to
// grey for every arabic reader. `closed` stays grey rather than red: it
// covers HRMS's "Hold" as well as "Rejected", and a red chip would announce
// a rejection the applicant has not been told about.
const STAGE_COLOR: Record<string, ChipColor> = {
	received: 'default',
	under_review: 'info',
	shortlisted: 'primary',
	closed: 'default',
	accepted: 'success'
};

function StatCard({
	icon,
	label,
	value,
	loading
}: {
	icon: React.ReactNode;
	label: string;
	value: number;
	loading: boolean;
}) {
	return (
		<Card sx={{ height: '100%' }}>
			<CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
				<Box
					sx={{
						width: 56,
						height: 56,
						borderRadius: '50%',
						display: 'flex',
						alignItems: 'center',
						justifyContent: 'center',
						backgroundColor: 'secondary.main',
						color: 'secondary.contrastText',
						flexShrink: 0
					}}
				>
					{icon}
				</Box>
				<Box>
					<Typography color="text.secondary" variant="body2">
						{label}
					</Typography>
					{loading ? <Skeleton width={40} height={36} /> : <Typography variant="h4">{value}</Typography>}
				</Box>
			</CardContent>
		</Card>
	);
}

function ApplicationsCard({ applications, lang }: { applications: JobApplication[]; lang: Lang }) {
	const s = t(lang);
	// Rendered only when there is something in it: the portal's audience is
	// pest-control customers, and an empty "My Applications" card on every
	// one of their dashboards would be noise.
	if (!applications.length) return null;

	const dateFormat = new Intl.DateTimeFormat(lang === 'ar' ? 'ar' : 'en-GB', {
		day: 'numeric',
		month: 'short',
		year: 'numeric'
	});

	return (
		<Card sx={{ mt: 3 }}>
			<CardContent>
				<Typography variant="h6" sx={{ mb: 2 }}>
					{s.myApplications}
				</Typography>
				{applications.map((application, index) => (
					<Box key={application.name}>
						{index > 0 && <Divider sx={{ my: 1.5 }} />}
						<Stack
							direction={{ xs: 'column', sm: 'row' }}
							sx={{ alignItems: { sm: 'center' }, gap: 1 }}
						>
							<Box sx={{ flexGrow: 1, minWidth: 0 }}>
								<Typography variant="subtitle1">
									{application.job_url ? (
										<Link href={application.job_url} underline="hover" color="inherit">
											{application.title}
										</Link>
									) : (
										application.title
									)}
								</Typography>
								{application.applied_on && (
									<Typography variant="body2" color="text.secondary">
										{s.appliedOn} {dateFormat.format(new Date(application.applied_on))}
									</Typography>
								)}
							</Box>
							<StatusChip
								status={application.stage_label}
								color={STAGE_COLOR[application.stage] ?? 'default'}
							/>
						</Stack>
					</Box>
				))}
			</CardContent>
		</Card>
	);
}

export default function Overview({
	lang,
	applications
}: {
	lang: Lang;
	applications: JobApplication[];
}) {
	const s = t(lang);
	const [orders, setOrders] = useState<PortalListRow[]>([]);
	const [quotations, setQuotations] = useState<PortalListRow[]>([]);
	const [invoices, setInvoices] = useState<PortalListRow[]>([]);
	const [loading, setLoading] = useState(true);

	useEffect(() => {
		let cancelled = false;
		Promise.all([
			fetchPortalRows('Sales Order'),
			fetchPortalRows('Quotation'),
			fetchPortalRows('Sales Invoice')
		]).then(([o, q, i]) => {
			if (cancelled) return;
			setOrders(o);
			setQuotations(q);
			setInvoices(i);
			setLoading(false);
		});
		return () => {
			cancelled = true;
		};
	}, []);

	const statusBreakdown = useMemo(() => {
		const counts = new Map<string, number>();
		[...orders, ...quotations, ...invoices].forEach((row) => {
			const status = row.status ?? 'Unknown';
			counts.set(status, (counts.get(status) ?? 0) + 1);
		});
		return Array.from(counts.entries()).map(([label, value], id) => ({ id, label, value }));
	}, [orders, quotations, invoices]);

	const hasAnyData = orders.length + quotations.length + invoices.length > 0;

	return (
		<Box>
			<Typography variant="h4" sx={{ mb: 3 }}>
				{s.welcomeBack}
			</Typography>

			<Grid container spacing={3} sx={{ mb: 3 }}>
				<Grid item xs={12} sm={4}>
					<StatCard icon={<ReceiptLongIcon />} label={s.navOrders} value={orders.length} loading={loading} />
				</Grid>
				<Grid item xs={12} sm={4}>
					<StatCard icon={<RequestQuoteIcon />} label={s.navQuotations} value={quotations.length} loading={loading} />
				</Grid>
				<Grid item xs={12} sm={4}>
					<StatCard icon={<DescriptionIcon />} label={s.navInvoices} value={invoices.length} loading={loading} />
				</Grid>
			</Grid>

			<Card>
				<CardContent>
					<Typography variant="h6" sx={{ mb: 2 }}>
						{s.statusBreakdown}
					</Typography>
					{loading && <Skeleton height={260} />}
					{!loading && !hasAnyData && (
						<Typography color="text.secondary">{s.noStatusDataYet}</Typography>
					)}
					{!loading && hasAnyData && (
						<PieChart
							series={[{ data: statusBreakdown, innerRadius: 60, paddingAngle: 2, cornerRadius: 6 }]}
							height={260}
						/>
					)}
				</CardContent>
			</Card>

			<ApplicationsCard applications={applications} lang={lang} />
		</Box>
	);
}
