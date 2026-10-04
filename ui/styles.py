"""Tokenized light and dark surfaces for the operational workspaces."""
import streamlit as st
from ui.themes import palette, theme_name


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
__THEME_TOKENS__
html,body,[data-testid="stApp"] {background:var(--canvas);color:var(--text);font-family:Inter,'Segoe UI',system-ui,sans-serif;}
[data-testid="stApp"] {background:var(--page);}
h1,h2,h3,h4,p,span {letter-spacing:0;}
h1,h2,h3,h4,[data-testid="stMarkdownContainer"],[data-testid="stExpander"],[data-testid="stWidgetLabel"] {color:var(--text);}
[data-testid="stCaptionContainer"] {color:var(--secondary);}
h1,h2,h3,h4,[data-testid="stMarkdownContainer"],[data-testid="stWidgetLabel"],button,input,textarea {font-family:Inter,'Segoe UI',system-ui,sans-serif;}
#MainMenu,footer,[data-testid="stToolbar"] {visibility:hidden;}
[data-testid="stHeader"] {background:transparent;}
[data-testid="stExpandSidebarButton"],[data-testid="stExpandSidebarButton"] * {visibility:visible!important;}
.block-container {max-width:1860px;padding:2rem 2rem 1.5rem;}
[data-testid="stVerticalBlock"] {gap:18px;}
[data-testid="stSidebar"] {background:var(--sidebar);border-right:1px solid var(--border);min-width:255px;max-width:290px;}
[data-testid="stSidebarContent"] {padding:1.5rem 1.2rem;}
[data-testid="stWidgetLabel"] p {font-size:12px;font-weight:600;color:var(--secondary);}
[data-testid="stTextArea"] textarea,[data-testid="stTextInput"] input {background:var(--canvas);color:var(--text);font-size:14px;line-height:1.7;}
[data-testid="stTextAreaRootElement"] {background:var(--canvas);border:1px solid var(--border);border-radius:8px;}
[data-testid="stTextInputRootElement"] {background:var(--input);border:1px solid var(--border);color:var(--text);}
[data-testid="stTextInputRootElement"] input {background:transparent;color:var(--text);}
[data-testid="stTextInputRootElement"] button {color:var(--secondary);}
[data-testid="stTextInputRootElement"]:focus-within,[data-testid="stTextAreaRootElement"]:focus-within {border-color:var(--blue);}
[data-testid="stSelectbox"] [role="group"] {background:var(--input);border:1px solid var(--border);border-radius:8px;}
[data-testid="stSelectbox"] input,[data-testid="stSelectbox"] button {color:var(--text);}
[data-testid="stSelectbox"] input:disabled,[data-testid="stTextInput"] input:disabled,[data-testid="stTextArea"] textarea:disabled {color:var(--muted);-webkit-text-fill-color:var(--muted);opacity:1;}
[data-testid="stSelectbox"] input::placeholder {color:var(--muted);}
[data-baseweb="input"],[data-baseweb="textarea"] {background:var(--input);border-color:var(--border);}
[data-baseweb="select"] {color:var(--text);}
[data-baseweb="select"] > div {background:var(--canvas);border-color:var(--border);border-radius:8px;font-size:14px;}
[role="listbox"],[data-baseweb="menu"] {background:var(--surface);color:var(--text);}
[data-testid="stSelectboxVirtualDropdown"] {background:var(--surface);border:1px solid var(--border);border-radius:8px;box-shadow:var(--shadow);}
[role="option"] {background:var(--surface);color:var(--text);}
[role="option"]:hover,[role="option"][aria-selected="true"] {background:var(--raised);color:var(--blue);}
[data-testid="stSegmentedControl"] button,[data-testid="stButtonGroup"] button {background:var(--surface);color:var(--secondary);border-color:var(--border);}
[data-testid="stSegmentedControl"] button[aria-pressed="true"],[data-testid="stButtonGroup"] button:is([aria-pressed="true"],[aria-checked="true"]) {background:var(--blue-surface);color:var(--blue);border-color:var(--blue-border);}
button [data-testid="stMarkdownContainer"] {color:inherit;}
[data-testid="stButtonGroup"] button:is([aria-pressed="true"],[aria-checked="true"]) :is([data-testid="stIconMaterial"],[data-testid="stMarkdownContainer"]) {color:var(--blue);}
[data-testid="stSidebarCollapseButton"] button,[data-testid="stExpandSidebarButton"] {color:var(--secondary);background:transparent;}
[data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"],[data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"] {color:var(--secondary);}
[data-testid="stCheckbox"] label,[data-testid="stToggle"] label,[data-testid="stSlider"] {color:var(--secondary);}
[data-testid="stCheckbox"] label p,[data-testid="stToggle"] label p {color:var(--secondary);}
[data-testid="stMarkdownContainer"] a {color:var(--blue);}
[data-testid="stMarkdownContainer"] code {background:var(--raised);color:var(--teal);}
[data-testid="stMarkdownContainer"] pre {background:var(--raised);color:var(--text);}
:is(button,input,textarea,[role="combobox"]):focus-visible {outline:2px solid var(--blue);outline-offset:2px;}
[data-testid="stButton"] button,[data-testid="stDownloadButton"] button {border-radius:8px;border:1px solid var(--border);background:var(--surface);color:var(--text);min-height:42px;font-size:13px;font-weight:500;transition:background .18s,border-color .18s,box-shadow .18s,transform .18s;}
[data-testid="stButton"] button:hover,[data-testid="stDownloadButton"] button:hover {border-color:var(--border);color:var(--blue);background:var(--hover);}
[data-testid="stButton"] button[kind="primary"] {background:var(--primary-gradient);border:0;color:white;box-shadow:0 4px 12px rgba(37,99,235,.16);}
[data-testid="stButton"] button[kind="primary"]:hover {background:var(--primary-hover-gradient);color:white;transform:translateY(-1px);box-shadow:0 6px 16px rgba(37,99,235,.2);}
[data-testid="stButton"] button:disabled {opacity:.42;}
[data-testid="stExpander"] {border:1px solid var(--border);border-radius:8px;background:var(--surface);}
[data-testid="stExpander"] summary {background:var(--surface);color:var(--text);}
[data-testid="stExpander"] summary:hover {background:var(--raised);color:var(--text);}
[data-testid="stExpander"] details summary p {font-size:13px;font-weight:500;}
[data-testid="stExpander"] h1 {font-size:22px;}[data-testid="stExpander"] h2 {font-size:17px;}
[data-testid="stTabs"] [role="tablist"] {gap:8px;border-bottom:1px solid var(--border);overflow-x:auto;}
[data-testid="stTabs"] [role="tab"] {padding:13px 17px;min-height:52px;border-radius:6px 6px 0 0;color:var(--secondary);border-bottom:2px solid transparent;flex-shrink:0;transition:background .18s,color .18s;}
[data-testid="stTabs"] [role="tab"] p {font-size:13px;font-weight:600;margin:0;}
[data-testid="stTabs"] [role="tab"]:hover {color:var(--text);background:var(--hover);}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {color:var(--blue);border-bottom-color:var(--blue);background:var(--accent-gradient);}
[data-testid="stTabs"] [role="tab"]:before {font-size:11px;color:var(--gold);margin-right:9px;font-weight:600;}
[data-testid="stTabs"] [role="tab"]:nth-child(1):before {content:'01';}
[data-testid="stTabs"] [role="tab"]:nth-child(2):before {content:'02';}
[data-testid="stTabs"] [role="tab"]:nth-child(3):before {content:'03';}
[data-testid="stTabs"] [role="tab"]:nth-child(4):before {content:'04';}
[data-testid="stTabs"] [role="tabpanel"] {padding-top:22px;}
[data-baseweb="tab-highlight"] {background:var(--blue);height:2px;}
[data-testid="stSegmentedControl"] button {font-size:12px;}
[data-testid="stDeckGlJsonChart"] {border:1px solid var(--border);border-radius:8px;overflow:hidden;background:var(--canvas);box-shadow:var(--shadow);}
/* Keep live readouts steady during fragment refreshes; controls retain their busy states. */
.st-key-live-operations [data-testid="stElementContainer"][data-stale="true"]:has([data-testid="stMarkdown"],[data-testid="stDeckGlJsonChart"]) {opacity:1;}
.hero {display:flex;justify-content:space-between;align-items:center;gap:24px;padding:4px 0 24px;}
.eyebrow {font-size:10.5px;font-weight:600;color:var(--blue);margin-bottom:9px;}
.hero .eyebrow {color:var(--teal);}
.hero h1 {font-size:32px;font-weight:700;margin:0 0 8px;line-height:1.2;color:var(--text);}
.hero h1,.workspace-heading h2,.orchestration-phase h3 {padding:0!important;}
[data-testid="stHeaderActionElements"] {display:none;}
.subline {font-size:13px;color:var(--secondary);line-height:1.6;}
.network-status {display:grid;grid-template-columns:repeat(4,minmax(70px,1fr));gap:22px;flex-shrink:0;}
.network-status > div {padding-left:14px;border-left:1px solid var(--border);}
.network-status label,.metric-label,.control-label,.detail-grid label,.candidate-row label,.decision-policy label {font-size:10.5px;font-weight:500;color:var(--muted);display:block;}
.network-status strong {display:block;font-size:12px;font-weight:600;margin-top:8px;}
.online-dot {display:inline-block;width:6px;height:6px;background:var(--green);border-radius:50%;margin-right:6px;}
.command-brand {display:flex;gap:12px;align-items:center;margin-bottom:22px;}
.brand-mark {width:42px;height:42px;display:grid;place-items:center;background:var(--brand-gradient);border:1px solid var(--border);border-top:2px solid var(--gold-edge);border-radius:8px;color:var(--blue);font-size:16px;font-weight:700;}
.brand-title {font-size:15px;font-weight:600;}.small {font-size:11px;color:var(--muted);margin-top:5px;}
.sidebar-status {padding:12px 0 17px;border-bottom:1px solid var(--border);font-size:11px;}
.sidebar-status strong {color:var(--green);font-weight:500;}.sidebar-status p {font-size:12px;color:var(--secondary);margin:10px 0 0;}
.control-label {margin:22px 0 6px;font-size:12px;font-weight:600;color:var(--text);}
.environment-value strong {font-size:25px;font-weight:600;}.environment-value span {font-size:12px;color:var(--secondary);}
.section-heading {display:flex;align-items:center;justify-content:space-between;gap:12px;margin:4px 0 14px;}
.section-heading b {font-size:16px;font-weight:600;}.section-heading > span {font-size:10.5px;color:var(--muted);}
.section-index {font-size:11px;color:var(--gold);margin-right:10px;font-weight:600;}
.workspace-heading {margin-bottom:24px;}.workspace-heading h2 {font-size:24px;margin:0 0 8px;font-weight:600;}.workspace-heading p {font-size:13px;color:var(--secondary);margin:0;line-height:1.7;}
.node-meta {font-size:11px;color:var(--muted);line-height:1.8;}.node-meta b {color:var(--secondary);font-weight:400;}
.mission-line {display:flex;justify-content:space-between;align-items:center;gap:12px;font-size:12px;line-height:1.7;flex-wrap:wrap;}
.mission-line > span {color:var(--secondary);min-width:0;overflow-wrap:anywhere;}
.mission-line > span > b {color:var(--gold);font-weight:600;}
.pill {display:inline-block;font-size:10px;font-weight:600;border:1px solid var(--border);border-radius:4px;padding:5px 8px;white-space:nowrap;line-height:1.3;background:var(--raised);}
.pill.green {color:var(--green);background:var(--success-surface);border-color:var(--success-border);}
.pill.blue {color:var(--blue);background:var(--blue-surface);border-color:var(--blue-border);}
.pill.cyan {color:var(--teal);background:var(--teal-surface);border-color:var(--teal-border);}
.pill.amber,.pill.gold {color:var(--gold);background:var(--warning-surface);border-color:var(--warning-border);}
.pill.red {color:var(--red);background:var(--danger-surface);border-color:var(--danger-border);}
.authorization {background:var(--authorization-gradient);border-left:3px solid var(--teal);padding:20px 24px;min-height:220px;}
.authorization.standby-auth {border-color:var(--blue);}.authorization.pass {border-left-color:var(--gold-edge);}
.auth-state {font-size:22px;font-weight:600;margin:6px 0 10px;}
.authorization p {font-size:13px;color:var(--secondary);line-height:1.7;margin:0 0 16px;}
.auth-grid {display:grid;grid-template-columns:1fr 1fr;gap:16px 20px;}.auth-grid label {font-size:10px;color:var(--muted);display:block;margin-bottom:6px;}.auth-grid strong {font-size:13px;font-weight:500;}
.authorization.compact {min-height:0;padding:18px 20px;}
.authorization.compact .eyebrow {margin-bottom:0;font-size:10px;}
.authorization.compact .auth-grid {gap:12px 16px;margin-top:16px;}
.authorization.compact .auth-grid strong {font-size:12px;}
.authorization.compact .auth-state {font-size:15px;margin:0;}
.authorization-seal {font-size:11px;color:var(--green);border-top:1px solid var(--success-border);padding-top:12px;margin-top:16px;}
.hud {display:grid;grid-template-columns:1.3fr repeat(5,minmax(0,1fr));gap:12px;margin:4px 0 2px;}
.metric-card {background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:18px 16px;min-width:0;min-height:110px;box-shadow:var(--shadow);}
.metric-card:first-child {background:var(--accent-gradient);border-top:2px solid var(--blue-border);}
.metric-card:nth-child(5) {border-top:2px solid var(--teal-border);}
.metric-card:last-child {border-top:2px solid var(--warning-border);}
.metric-value {font-size:24px;font-weight:600;line-height:1.25;margin:10px 0 7px;overflow-wrap:anywhere;}
.metric-sub {font-size:11px;line-height:1.6;color:var(--secondary);}
.cyan,.neon-cyan {color:var(--teal);}.blue {color:var(--blue);}.green {color:var(--green);}.amber {color:var(--amber);}.red {color:var(--red);}.muted {color:var(--secondary);}.gold {color:var(--gold);}
.standby-band {display:flex;justify-content:space-between;align-items:center;gap:20px;border-left:3px solid var(--blue-border);padding:20px 22px;background:var(--accent-gradient);}
.standby-band strong {font-size:16px;font-weight:600;}.standby-band p {font-size:13px;color:var(--secondary);margin:7px 0 0;line-height:1.6;}
.standby {font-size:13px;line-height:1.8;color:var(--secondary);padding:20px 0;}
.map-bar {display:flex;justify-content:space-between;align-items:center;gap:12px;}
.map-title {font-size:16px;font-weight:600;}.map-title small {display:block;font-size:11px;color:var(--muted);margin-top:6px;font-weight:400;}
.map-legend {display:flex;gap:12px;font-size:10px;color:var(--secondary);}.map-legend i {display:inline-block;width:6px;height:6px;border-radius:50%;margin-right:5px;}
.map-status {display:flex;align-items:center;gap:8px;margin:5px 0 8px;flex-wrap:wrap;}
.map-status .pill {font-size:9px;background:var(--surface);border-color:var(--border);}
.telemetry-group {padding:16px 0;border-top:1px solid var(--border);}
.telemetry-group h4 {font-size:10px;color:var(--muted);font-weight:600;margin:0 0 14px;}
.telemetry-row {display:flex;justify-content:space-between;gap:12px;font-size:12px;margin:11px 0;line-height:1.6;}
.telemetry-row span {color:var(--secondary);flex-shrink:0;max-width:48%;}
.telemetry-row strong {font-weight:500;text-align:right;min-width:0;overflow-wrap:anywhere;}
.aircraft-name {font-size:25px;font-weight:600;margin:14px 0 7px;}.aircraft-role {font-size:12px;color:var(--secondary);margin-bottom:18px;line-height:1.6;}
.phase-timeline {display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:8px;padding:18px 0;}
.phase-timeline > div {font-size:10px;color:var(--muted);border-top:2px solid var(--border);padding-top:10px;}
.phase-timeline span {display:block;margin-bottom:6px;font-size:10px;}
.phase-timeline .done {color:var(--green);border-color:var(--success-border);}.phase-timeline .current {color:var(--teal);border-color:var(--teal);}
.telemetry-strip {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:18px;border-top:1px solid var(--border);padding-top:20px;}
.telemetry-strip label {display:block;font-size:10px;color:var(--muted);margin-bottom:7px;}.telemetry-strip strong {font-size:12px;font-weight:500;}
.mission-progress {height:3px;background:var(--border);margin-top:12px;border-radius:2px;}.mission-progress i {display:block;height:100%;background:var(--teal);}
.notice {padding:14px 18px;border-left:2px solid currentColor;background:var(--surface);font-size:13px;line-height:1.8;}
.completion-strip {display:flex;align-items:center;justify-content:space-between;gap:16px;border-left:3px solid var(--green);background:var(--success-surface);padding:16px 20px;}
.completion-strip strong {font-size:12px;color:var(--green);font-weight:600;}.completion-strip span {font-size:12px;color:var(--secondary);}
.st-key-operator-assignment button {border-color:var(--blue-border);color:var(--blue);}
.st-key-abort-mission button:hover {border-color:var(--danger-border);color:var(--red);background:var(--danger-surface);}
.detail-grid {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;padding:14px 0;}.detail-grid strong {font-size:14px;display:block;margin-top:7px;font-weight:500;}
.fleet-summary {display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px;margin-bottom:28px;}
.fleet-summary > div {border-left:2px solid var(--border);padding:8px 16px;}.fleet-summary label {font-size:10px;color:var(--muted);display:block;}
.fleet-summary strong {font-size:27px;display:block;margin-top:8px;font-weight:600;}
.sector-strip {display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:16px;margin-bottom:28px;}
.sector-strip > div {border-bottom:1px solid var(--border);padding-bottom:14px;}.sector-strip label {font-size:10px;color:var(--muted);display:block;}.sector-strip strong {font-size:13px;margin-top:7px;display:block;font-weight:500;}
.registry-grid {display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-bottom:28px;}
.registry-item {border:1px solid var(--border);background:var(--surface);border-radius:8px;padding:20px;box-shadow:var(--shadow);}
.registry-item .role {font-size:13px;color:var(--secondary);margin:10px 0;}.registry-item .hub {font-size:11px;color:var(--muted);margin-bottom:18px;}
.specs {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;font-size:13px;}.specs label {font-size:10px;color:var(--muted);display:block;margin-bottom:6px;}
.candidate-row {display:grid;grid-template-columns:1.3fr .7fr 1fr .8fr;gap:14px;border:1px solid var(--border);border-radius:8px;background:var(--surface);padding:20px;margin-bottom:12px;align-items:center;}
.candidate-row.selected {border-left:3px solid var(--blue);background:var(--accent-gradient);}
.candidate-row.selected label,.candidate-row .cyan {color:var(--blue);}
.candidate-row strong {font-size:16px;}.candidate-row b {font-size:14px;display:block;margin:7px 0;font-weight:600;}
.candidate-row span,.candidate-row small {display:block;font-size:11px;color:var(--secondary);line-height:1.7;}.candidate-row label {overflow-wrap:anywhere;}
.registry-item:hover,.candidate-row:hover {border-color:var(--border);}
.rejection-row {display:grid;grid-template-columns:90px 1fr;gap:14px;font-size:12px;padding:14px 0;border-bottom:1px solid var(--border);}.rejection-row span {color:var(--secondary);line-height:1.7;}
.aircraft-comparison {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px;margin:20px 0;}
.aircraft-comparison > div {min-width:0;}.aircraft-comparison label,.comparison-delta label,.report-masthead label {display:block;font-size:10px;color:var(--muted);margin-bottom:12px;}
.aircraft-comparison strong {display:block;font-size:22px;color:var(--text);font-weight:600;}.aircraft-comparison > div:first-child strong {color:var(--blue);}
.aircraft-comparison dl {display:grid;grid-template-columns:minmax(0,1fr) auto;gap:12px;font-size:12px;margin:18px 0 0;}
.aircraft-comparison dt {color:var(--secondary);}.aircraft-comparison dd {margin:0;text-align:right;}
.comparison-delta {font-size:12px;line-height:1.9;color:var(--blue);padding:14px 0;}
.decision-policy {border-top:1px solid var(--border);padding-top:20px;margin-top:20px;}
.decision-policy strong {font-size:13px;display:block;color:var(--blue);margin-top:9px;}.decision-policy.override strong {color:var(--gold);}
.decision-policy p {font-size:12px;color:var(--secondary);line-height:1.8;margin-bottom:0;}
.orchestration {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:24px;margin-bottom:30px;}
.orchestration-phase {border-top:2px solid var(--phase-color);padding-top:18px;min-width:0;position:relative;}
.orchestration-phase[data-phase="understand"] {--phase-color:var(--blue);}.orchestration-phase[data-phase="optimize"] {--phase-color:var(--muted);}
.orchestration-phase[data-phase="navigate"] {--phase-color:var(--teal);}.orchestration-phase[data-phase="verify"] {--phase-color:var(--green);}
.orchestration-phase:not(:last-child):after {content:'>';position:absolute;right:-18px;top:20px;color:var(--border);}
.orchestration-phase h3 {font-size:17px;margin:0 0 18px;font-weight:600;}.orchestration-phase h3 .phase-number {color:var(--phase-color);font-size:11px;margin-right:9px;}
.agent-module {position:relative;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:18px;margin-bottom:14px;min-height:142px;box-shadow:var(--shadow);}
.agent-module .agent-title {font-size:13px;font-weight:600;display:block;margin-bottom:12px;}
.agent-module p {font-size:12px;line-height:1.8;color:var(--secondary);margin:11px 0 0;overflow-wrap:anywhere;}
.agent-module .execution {font-size:10.5px;color:var(--muted);margin-top:13px;}
.agent-module.processing {border-color:var(--blue-border);}.agent-module.blocked {border-left:3px solid var(--red);}
.agent-module:not(:last-child):after {content:'';position:absolute;bottom:-15px;left:23px;width:1px;height:14px;background:var(--border);}
.agent-title:before {content:'';display:inline-block;width:5px;height:5px;border-radius:50%;background:var(--border);margin:0 7px 2px 0;}
.agent-module.verified .agent-title:before {background:var(--green);}.agent-module.processing .agent-title:before {background:var(--blue);animation:processing-pulse 1.3s ease-in-out infinite;}
.agent-module.authorized {border-bottom:2px solid var(--gold-edge);background:var(--verified-gradient);}
.agent-module.authorized .pill {color:var(--gold);background:var(--warning-surface);border-color:var(--warning-border);}
.agent-output-label {font-size:10px;color:var(--muted);margin-top:14px;}
.analytics-band {border-top:1px solid var(--border);padding-top:26px;margin-top:22px;}
.analytics-score {font-size:28px;font-weight:600;margin:12px 0 9px;}.analytics-score small {font-size:12px;color:var(--secondary);font-weight:400;}
.bar-row {display:grid;grid-template-columns:130px minmax(0,1fr) 85px;gap:12px;align-items:center;font-size:12px;margin:17px 0;}
.bar-row > span {color:var(--secondary);}.bar-row > b {font-weight:500;text-align:right;}
.bar-track {height:5px;background:var(--border);border-radius:3px;overflow:hidden;}.bar-track i {display:block;height:100%;background:var(--blue);}
.risk-bars .bar-track i {background:var(--teal);}.risk-bars .elevated .bar-track i {background:var(--amber);}
.reason-list {padding:0;list-style:none;font-size:12px;line-height:1.8;}.reason-list li {margin:11px 0;color:var(--secondary);}.reason-list li:before {content:'+';color:var(--green);margin-right:10px;}
.timeline {margin:10px 0 26px;}.timeline-entry {display:grid;grid-template-columns:90px minmax(0,1fr) 85px;gap:16px;padding:17px 0;border-bottom:1px solid var(--border);font-size:12px;}
.timeline-entry time {color:var(--muted);font-variant-numeric:tabular-nums;}.timeline-entry b {font-size:13px;font-weight:500;}
.timeline-entry p {color:var(--secondary);line-height:1.7;margin:8px 0 0;}.timeline-entry .execution {color:var(--muted);text-align:right;}
.report-masthead {padding:24px 0 8px;}.report-masthead h3 {font-size:23px;font-weight:600;line-height:1.5;padding:0!important;margin:0;}
.report-summary {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:26px 28px;padding:26px 0;border-top:1px solid var(--border);border-bottom:1px solid var(--border);background:transparent;}
.report-summary label {display:block;font-size:12px;color:var(--secondary);margin-bottom:10px;}
.report-summary strong {font-size:14px;font-weight:500;line-height:1.8;overflow-wrap:anywhere;}
.report-summary small {display:block;font-size:11px;color:var(--muted);line-height:1.7;margin-top:8px;}
.safety-strip {display:flex;flex-wrap:wrap;gap:8px;padding:18px 0;}
.safety-strip .pill {color:var(--text);background:var(--surface);border:1px solid var(--border);border-left:2px solid var(--success-border);font-size:11px;font-weight:400;padding:8px 11px;}
.safety-strip .pill.red {border-left-color:var(--red);}.safety-strip .pill:last-child {border-bottom-color:var(--gold-edge);}
.report-document {font-size:13px;line-height:1.8;}
.audit-timeline {border-left:1px solid var(--border);margin-left:4px;padding-left:22px;}
.audit-timeline .timeline-entry {position:relative;border:0;grid-template-columns:90px minmax(0,1fr);padding:16px 0;}
.audit-timeline .timeline-entry:before {content:'';position:absolute;left:-26px;top:23px;width:7px;height:7px;border-radius:50%;background:var(--border);border:2px solid white;}
.bottom-note {font-size:10.5px;color:var(--muted);line-height:1.8;border-top:1px solid var(--border);padding-top:20px;margin-top:26px;}
@keyframes processing-pulse {50% {opacity:.4;}}
@media(max-width:1500px) {
 .network-status {grid-template-columns:repeat(2,minmax(80px,1fr));gap:14px 20px;}
 .hero h1 {font-size:30px;}.metric-card {padding:16px 13px;}.metric-value {font-size:21px;}
 .candidate-row {grid-template-columns:1.2fr .7fr 1fr;}.candidate-row > div:last-child {grid-column:1 / -1;display:flex;align-items:center;gap:12px;}
 .orchestration {gap:18px;}.agent-module {padding:15px;}.bar-row {grid-template-columns:115px minmax(0,1fr) 75px;}
}
@media(max-width:1150px) {
 .block-container {padding:2rem 1.2rem 1rem;}.hud {grid-template-columns:repeat(3,minmax(0,1fr));}
 .registry-grid {grid-template-columns:repeat(2,minmax(0,1fr));}.orchestration {grid-template-columns:repeat(2,minmax(0,1fr));}
 .orchestration-phase:nth-child(2):after {display:none;}.hero h1 {font-size:28px;}.network-status {gap:12px;}
}
@media(max-width:700px) {
 .block-container {padding:3rem 1rem 1rem;}.hero {align-items:flex-start;flex-direction:column;gap:22px;}
 .hero h1 {font-size:27px;}.network-status {grid-template-columns:repeat(4,minmax(0,1fr));width:100%;gap:8px;}
 .network-status > div {padding-left:0;border:0;}.network-status strong,.network-status label {font-size:10px;}
 .hud {grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;}.metric-value {font-size:22px;}
 .metric-card {min-height:110px;}.phase-timeline {grid-template-columns:repeat(4,minmax(0,1fr));}
 .telemetry-strip,.report-summary {grid-template-columns:repeat(2,minmax(0,1fr));}
 .registry-grid,.orchestration {grid-template-columns:1fr;}.orchestration-phase:after {display:none;}
 .fleet-summary,.sector-strip {grid-template-columns:repeat(3,minmax(0,1fr));}
 .candidate-row {grid-template-columns:repeat(2,minmax(0,1fr));}.candidate-row > div:last-child {grid-column:auto;display:block;}
 .timeline-entry {grid-template-columns:70px minmax(0,1fr);gap:10px;}.timeline-entry .execution {grid-column:2;text-align:left;}
 .standby-band,.completion-strip {align-items:flex-start;flex-direction:column;gap:12px;}
 .section-heading > span {max-width:40%;text-align:right;}.bar-row {grid-template-columns:105px minmax(0,1fr) 70px;gap:8px;}
 .authorization {padding:18px;}.map-legend {gap:8px;}.map-bar {flex-wrap:wrap;}
 .report-masthead h3 {font-size:20px;}.report-summary {gap:24px 16px;}
 .audit-timeline .timeline-entry {grid-template-columns:65px minmax(0,1fr);}
 .aircraft-comparison {gap:16px;}.aircraft-comparison dl {grid-template-columns:1fr;gap:5px;}
 .aircraft-comparison dd {text-align:left;margin-bottom:5px;}
}
@media(prefers-reduced-motion:reduce) {* {animation:none!important;transition:none!important;}}
</style>
"""


def theme_css(mode: str = "Light") -> str:
    tokens = ";".join(f"--{name}:{value}" for name, value in palette(mode).items())
    scheme = theme_name(mode).lower()
    return CSS.replace("__THEME_TOKENS__", f":root {{{tokens};color-scheme:{scheme};}}")


def inject_css():
    st.markdown(theme_css(st.session_state.get("theme", "Light")), unsafe_allow_html=True)
