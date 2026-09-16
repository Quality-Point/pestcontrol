import { Chip } from '@mui/material';

export type ChipColor = 'success' | 'error' | 'warning' | 'info' | 'primary' | 'default';

const STATUS_COLOR: Record<string, ChipColor> = {
	Paid: 'success',
	Completed: 'success',
	Closed: 'success',
	Draft: 'default',
	'To Bill': 'warning',
	'To Deliver and Bill': 'warning',
	Overdue: 'error',
	Cancelled: 'error',
	Unpaid: 'warning'
};

// `color` overrides the lookup. Job applications need it for two reasons:
// their label arrives already translated, so an english-keyed map would miss
// entirely in arabic, and their "Closed" means the opposite of the entry
// above — a Sales Invoice that is Closed is done, an application that is
// Closed is not good news, so it must not be green.
export default function StatusChip({ status, color }: { status?: string; color?: ChipColor }) {
	if (!status) return null;
	return <Chip label={status} color={color ?? STATUS_COLOR[status] ?? 'default'} size="small" />;
}
