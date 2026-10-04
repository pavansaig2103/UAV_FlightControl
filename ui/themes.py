"""Shared light/dark presentation tokens, independent of mission state."""

LIGHT = {
    "blue": "#2563eb", "teal": "#077786", "green": "#15803d", "gold": "#896524",
    "amber": "#ad6414", "red": "#c93553", "text": "#202632", "secondary": "#526074",
    "muted": "#647286", "border": "#e1e6ed", "surface": "#ffffff", "raised": "#f3f7fc",
    "canvas": "#f7f9fc", "input": "#f0f4f9", "hover": "#f5f9ff",
    "primary-gradient": "linear-gradient(115deg,#2563eb,#087f8c)",
    "primary-hover-gradient": "linear-gradient(115deg,#2866dc,#077786)",
    "page": "linear-gradient(125deg,#f3f6fc 0%,#ffffff 48%,#eff9f6 100%)",
    "sidebar": "linear-gradient(180deg,#ffffff,#f7f9fc)",
    "accent-gradient": "linear-gradient(110deg,#eaf2ff,#f2faf8)",
    "authorization-gradient": "linear-gradient(120deg,#eef4ff,#f0faf6)",
    "brand-gradient": "linear-gradient(135deg,#e8f0ff,#e3f5ef)",
    "verified-gradient": "linear-gradient(140deg,#fff,#f3faf5)",
    "success-surface": "#eef9f2", "success-border": "#d2ebdb",
    "warning-surface": "#fcf8ee", "warning-border": "#ebdfc5",
    "danger-surface": "#fff1f4", "danger-border": "#f2d5df",
    "blue-surface": "#eef4ff", "blue-border": "#d7e4fc",
    "teal-surface": "#eef8f8", "teal-border": "#d0e8e9", "gold-edge": "#bea36a",
    "shadow": "0 4px 18px rgba(40,58,86,.05)",
}

DARK = {
    **LIGHT,
    "blue": "#83b3ff", "teal": "#70d4d0", "green": "#82d4a0", "gold": "#d8ba79",
    "amber": "#edb75f", "red": "#ff98a9", "text": "#edf1f5", "secondary": "#c0c8d2",
    "muted": "#a4afbe", "border": "#363c44", "surface": "#1b1e22", "raised": "#23272d",
    "canvas": "#111315", "input": "#20242a", "hover": "#282f38",
    "page": "linear-gradient(125deg,#111315 0%,#17191c 48%,#14211f 100%)",
    "sidebar": "linear-gradient(180deg,#1b1e22,#16181b)",
    "accent-gradient": "linear-gradient(110deg,#243044,#21332f)",
    "authorization-gradient": "linear-gradient(120deg,#202b3a,#20332d)",
    "brand-gradient": "linear-gradient(135deg,#2a3647,#243c33)",
    "verified-gradient": "linear-gradient(140deg,#1b1e22,#22332a)",
    "success-surface": "#203629", "success-border": "#395744",
    "warning-surface": "#362e20", "warning-border": "#5c4e30",
    "danger-surface": "#3b252c", "danger-border": "#65404a",
    "blue-surface": "#233147", "blue-border": "#405679",
    "teal-surface": "#203637", "teal-border": "#3b595a", "gold-edge": "#b59a62",
    "shadow": "0 4px 18px rgba(0,0,0,.16)",
}

THEMES = {"Light": LIGHT, "Dark": DARK}
BASEMAP_STYLES = {
    "Light": "/app/static/daylight_basemap.json",
    "Dark": "/app/static/night_basemap.json",
}


def theme_name(value: str | None) -> str:
    return value if value in THEMES else "Light"


def palette(value: str | None) -> dict:
    return THEMES[theme_name(value)]


def rgb(color: str) -> list[int]:
    return [int(color[offset:offset + 2], 16) for offset in (1, 3, 5)]
