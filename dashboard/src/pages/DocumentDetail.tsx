import { Box, Card, CardContent, Typography, Button, Stack, Divider } from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBackIosNew';
import ArrowForwardIcon from '@mui/icons-material/ArrowForwardIos';
import PrintIcon from '@mui/icons-material/Print';
import dayjs from 'dayjs';
import 'dayjs/locale/ar';
import StatusChip from '../components/StatusChip';
import { t, type Lang } from '../i18n';

interface DocumentDetailProps {
	doc: Record<string, unknown>;
	backHref?: string;
	lang: Lang;
	printFormat?: string;
}

interface DocItem {
	item_code?: string;
	item_name?: string;
	qty?: number;
	rate?: number;
	amount?: number;
}

export default function DocumentDetail({ doc, backHref, lang, printFormat }: DocumentDetailProps) {
	const s = t(lang);
	const currency = (doc.currency as string | undefined) ?? '';
	const items = (doc.items as DocItem[] | undefined) ?? [];
	const isRtl = lang === 'ar';
	const printUrl = `/printview?doctype=${encodeURIComponent(String(doc.doctype))}&name=${encodeURIComponent(String(doc.name))}&format=${encodeURIComponent(printFormat ?? '')}`;

	return (
		<Box>
			<Stack direction="row" justifyContent="space-between" sx={{ mb: 2 }}>
				<Button
					startIcon={isRtl ? <ArrowForwardIcon /> : <ArrowBackIcon />}
					component="a"
					href={backHref ?? '/portal'}
				>
					{s.back}
				</Button>
				<Button startIcon={<PrintIcon />} component="a" href={printUrl} target="_blank" rel="noopener noreferrer">
					{s.print}
				</Button>
			</Stack>

			<Card>
				<CardContent sx={{ p: 4 }}>
					<Stack direction="row" justifyContent="space-between" alignItems="flex-start" sx={{ mb: 3 }}>
						<Box>
							<Typography variant="h4">{String(doc.name ?? '')}</Typography>
							<Typography color="text.secondary">
								{dayjs((doc.transaction_date ?? doc.posting_date) as string)
									.locale(lang)
									.format('DD MMMM YYYY')}
							</Typography>
						</Box>
						<StatusChip status={doc.status as string | undefined} />
					</Stack>

					<Divider sx={{ mb: 3 }} />

					<Stack spacing={1.5} sx={{ mb: 3 }}>
						{items.map((item, idx) => (
							<Stack key={idx} direction="row" justifyContent="space-between">
								<Typography>
									{item.item_name ?? item.item_code} × {item.qty}
								</Typography>
								<Typography sx={{ fontWeight: 600 }}>
									{currency} {(item.amount ?? 0).toLocaleString()}
								</Typography>
							</Stack>
						))}
					</Stack>

					<Divider sx={{ mb: 2 }} />

					<Stack direction="row" justifyContent="space-between">
						<Typography variant="h6">{s.grandTotal}</Typography>
						<Typography variant="h6" color="secondary.main">
							{currency} {((doc.grand_total as number | undefined) ?? 0).toLocaleString()}
						</Typography>
					</Stack>
				</CardContent>
			</Card>
		</Box>
	);
}
