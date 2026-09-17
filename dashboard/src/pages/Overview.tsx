import { useEffect, useMemo, useState } from 'react';
import { Box, Card, CardContent, Typography, Grid, Skeleton } from '@mui/material';
import { PieChart } from '@mui/x-charts/PieChart';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import RequestQuoteIcon from '@mui/icons-material/RequestQuote';
import DescriptionIcon from '@mui/icons-material/Description';
import { fetchPortalRows, type PortalListRow } from '../api/portal';
import { t, type Lang } from '../i18n';

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

export default function Overview({ lang }: { lang: Lang }) {
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
		</Box>
	);
}
