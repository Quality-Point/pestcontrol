import { Box, Card, CardContent, Typography, Divider, Link, Stack } from '@mui/material';
import type { JobApplication } from '../api/portal';
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

export default function MyJobsPage({ applications, lang }: { applications: JobApplication[]; lang: Lang }) {
	const s = t(lang);
	const dateFormat = new Intl.DateTimeFormat(lang === 'ar' ? 'ar' : 'en-GB', {
		day: 'numeric',
		month: 'short',
		year: 'numeric'
	});

	return (
		<Box>
			<Typography variant="h4" sx={{ mb: 3 }}>
				{s.navMyJobs}
			</Typography>

			<Card>
				<CardContent>
					{applications.length === 0 ? (
						<Box sx={{ py: 4, textAlign: 'center' }}>
							<Typography color="text.secondary">{s.noApplicationsYet}</Typography>
						</Box>
					) : (
						applications.map((application, index) => (
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
						))
					)}
				</CardContent>
			</Card>
		</Box>
	);
}
