import { useMemo, useState } from 'react';
import { CacheProvider } from '@emotion/react';
import {
	ThemeProvider,
	CssBaseline,
	Box,
	AppBar,
	Toolbar,
	Typography,
	Drawer,
	List,
	ListItemButton,
	ListItemIcon,
	ListItemText,
	IconButton,
	Avatar,
	Tooltip,
	useMediaQuery
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import HomeIcon from '@mui/icons-material/Home';
import DashboardIcon from '@mui/icons-material/SpaceDashboard';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import RequestQuoteIcon from '@mui/icons-material/RequestQuote';
import DescriptionIcon from '@mui/icons-material/Description';
import PersonIcon from '@mui/icons-material/Person';
import { createDashboardTheme } from './theme';
import { createEmotionCache } from './emotionCache';
import { getInitials } from './utils/initials';
import { t, type Lang } from './i18n';
import Overview from './pages/Overview';
import PortalDocumentList from './components/PortalDocumentList';
import DocumentDetail from './pages/DocumentDetail';
import AccountPage from './pages/AccountPage';
import type { PortalListRow } from './api/portal';

export type PageType = 'overview' | 'list' | 'detail' | 'account';

const DRAWER_WIDTH = 260;

interface AppProps {
	direction: 'ltr' | 'rtl';
	lang: Lang;
	pageType: PageType;
	doctype?: string;
	docName?: string;
	printFormat?: string;
	listRows: PortalListRow[];
	detailDoc?: Record<string, unknown>;
	account: {
		fullName?: string;
		email?: string;
		avatarUrl?: string;
	};
}

const LIST_META: Record<string, { titleKey: 'navOrders' | 'navQuotations' | 'navInvoices'; basePath: string }> = {
	'Sales Order': { titleKey: 'navOrders', basePath: '/orders' },
	Quotation: { titleKey: 'navQuotations', basePath: '/quotations' },
	'Sales Invoice': { titleKey: 'navInvoices', basePath: '/invoices' }
};

function currentPath() {
	return window.location.pathname.replace(/\/+$/, '') || '/';
}

function DashboardShell(props: AppProps) {
	const isDesktop = useMediaQuery('(min-width:900px)');
	const [mobileOpen, setMobileOpen] = useState(false);
	const path = currentPath();
	const s = t(props.lang);

	const navItems = [
		{ href: '/portal', label: s.navOverview, icon: <DashboardIcon /> },
		{ href: '/orders', label: s.navOrders, icon: <ReceiptLongIcon /> },
		{ href: '/quotations', label: s.navQuotations, icon: <RequestQuoteIcon /> },
		{ href: '/invoices', label: s.navInvoices, icon: <DescriptionIcon /> },
		{ href: '/me', label: s.navAccount, icon: <PersonIcon /> }
	];

	const nav = (
		<List sx={{ pt: 2 }}>
			{navItems.map((item) => {
				const active = item.href === '/portal' ? path === '/portal' : path.startsWith(item.href);
				return (
					<ListItemButton
						key={item.href}
						component="a"
						href={item.href}
						sx={{
							mx: 1,
							borderRadius: 3,
							...(active && {
								backgroundColor: 'secondary.main',
								color: 'secondary.contrastText',
								'& .MuiListItemIcon-root': { color: 'secondary.contrastText' }
							})
						}}
					>
						<ListItemIcon>{item.icon}</ListItemIcon>
						<ListItemText primary={item.label} />
					</ListItemButton>
				);
			})}
		</List>
	);

	const listMeta = props.doctype ? LIST_META[props.doctype] : undefined;

	return (
		<Box
			sx={{
				display: 'flex',
				// The Drawer's Paper renders position:fixed even for
				// variant="permanent" (confirmed in MUI's own source) — flex
				// order/direction has no effect on a fixed element's own
				// position, but empirically this row-reverse + the main
				// content's explicit width (not just flexGrow) together are
				// what's needed for the layout to not overlap/clip in RTL;
				// removing either reintroduces clipping on the leading edge.
				flexDirection: props.direction === 'rtl' ? 'row-reverse' : 'row',
				minHeight: '100vh'
			}}
		>
			<AppBar position="fixed" sx={{ zIndex: (t) => t.zIndex.drawer + 1 }} elevation={0}>
				<Toolbar>
					{!isDesktop && (
						<IconButton edge="start" onClick={() => setMobileOpen(true)} sx={{ mr: 2 }}>
							<MenuIcon />
						</IconButton>
					)}
					<Typography variant="h6" component="div" sx={{ fontWeight: 700, flexGrow: 1 }}>
						{s.appTitle}
					</Typography>

					<Tooltip title={s.homeTooltip}>
						<IconButton component="a" href="/" sx={{ color: 'inherit' }}>
							<HomeIcon />
						</IconButton>
					</Tooltip>
					<Tooltip title={s.accountTooltip}>
						<IconButton component="a" href="/me" sx={{ ml: 1 }}>
							<Avatar
								src={props.account.avatarUrl}
								sx={{ width: 32, height: 32, bgcolor: 'secondary.main', fontSize: 14 }}
							>
								{getInitials(props.account.fullName, props.account.email)}
							</Avatar>
						</IconButton>
					</Tooltip>
				</Toolbar>
			</AppBar>

			<Drawer
				variant={isDesktop ? 'permanent' : 'temporary'}
				anchor={props.direction === 'rtl' ? 'right' : 'left'}
				open={isDesktop ? true : mobileOpen}
				onClose={() => setMobileOpen(false)}
				sx={{
					width: DRAWER_WIDTH,
					flexShrink: 0,
					'& .MuiDrawer-paper': { width: DRAWER_WIDTH, boxSizing: 'border-box' }
				}}
			>
				<Toolbar />
				{nav}
			</Drawer>

			<Box
				component="main"
				sx={{
					flexGrow: 1,
					minWidth: 0,
					p: { xs: 2, md: 4 },
					width: { md: `calc(100% - ${DRAWER_WIDTH}px)` }
				}}
			>
				<Toolbar />
				{props.pageType === 'overview' && <Overview lang={props.lang} />}
				{props.pageType === 'list' && listMeta && (
					<PortalDocumentList
						rows={props.listRows}
						title={s[listMeta.titleKey]}
						basePath={listMeta.basePath}
						lang={props.lang}
					/>
				)}
				{props.pageType === 'detail' && props.detailDoc && (
					<DocumentDetail
						doc={props.detailDoc}
						backHref={props.doctype ? LIST_META[props.doctype]?.basePath : undefined}
						lang={props.lang}
						printFormat={props.printFormat}
					/>
				)}
				{props.pageType === 'account' && <AccountPage {...props.account} lang={props.lang} />}
			</Box>
		</Box>
	);
}

export default function App(props: AppProps) {
	const theme = useMemo(() => createDashboardTheme(props.direction), [props.direction]);
	const cache = useMemo(() => createEmotionCache(props.direction), [props.direction]);

	return (
		<CacheProvider value={cache}>
			<ThemeProvider theme={theme}>
				<CssBaseline />
				<DashboardShell {...props} />
			</ThemeProvider>
		</CacheProvider>
	);
}
