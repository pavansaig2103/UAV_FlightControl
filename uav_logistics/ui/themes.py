"""Shared light/dark presentation tokens, independent of mission state."""

LIGHT = {
    "blue": "#245fd0", "teal": "#08777d", "green": "#197847", "gold": "#896524",
    "amber": "#a45f16", "red": "#b9364d", "text": "#172434", "secondary": "#52687d",
    "muted": "#586e83", "border": "#dce5ee", "surface": "#ffffff", "raised": "#f3f7fb",
    "canvas": "#f4f7fa", "input": "#f8fafc", "hover": "#f0f5ff",
    "strong-border": "#cbd8e6", "accent-blue": "#3f7cf4", "steel": "#526f98",
    "map-route": "#3d85f5", "map-hub": "#27915f", "map-hospital": "#d74e64",
    "map-destination": "#b08a3e", "map-aircraft": "#3f7cf4", "map-waypoint": "#178d98",
    "primary-gradient": "linear-gradient(115deg,#2563eb,#087f8c)",
    "primary-hover-gradient": "linear-gradient(115deg,#2866dc,#077786)",
    "page": "#f4f7fa",
    "sidebar": "#f5f8fb",
    "accent-gradient": "linear-gradient(110deg,#eaf2ff,#f2faf8)",
    "authorization-gradient": "linear-gradient(135deg,#f2f7ff,#f3fbf8)",
    "brand-gradient": "#eaf1ff",
    "verified-gradient": "linear-gradient(140deg,#fff,#f3faf5)",
    "success-surface": "#eef9f2", "success-border": "#d2ebdb",
    "warning-surface": "#fcf8ee", "warning-border": "#ebdfc5",
    "danger-surface": "#fff1f4", "danger-border": "#f2d5df",
    "blue-surface": "#eef4ff", "blue-border": "#d7e4fc",
    "teal-surface": "#eef8f8", "teal-border": "#d0e8e9", "gold-edge": "#bea36a",
    "shadow": "0 6px 20px rgba(30,55,80,.06)",
    "hero-shadow": "0 10px 28px rgba(30,55,80,.08)",
}

DARK = {
    **LIGHT,
    "blue": "#83b3ff", "teal": "#70d4d0", "green": "#82d4a0", "gold": "#d8ba79",
    "amber": "#edb75f", "red": "#ff98a9", "text": "#edf1f5", "secondary": "#c0c8d2",
    "muted": "#a4afbe", "border": "#363c44", "surface": "#1b1e22", "raised": "#23272d",
    "canvas": "#111315", "input": "#20242a", "hover": "#282f38",
    "strong-border": "#4a5563", "accent-blue": "#83b3ff", "steel": "#a3b7d1",
    "map-route": "#83b3ff", "map-hub": "#82d4a0", "map-hospital": "#ff98a9",
    "map-destination": "#d8ba79", "map-aircraft": "#83b3ff", "map-waypoint": "#70d4d0",
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
    "hero-shadow": "0 10px 28px rgba(0,0,0,.22)",
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
