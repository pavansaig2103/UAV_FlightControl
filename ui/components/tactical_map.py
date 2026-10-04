"""Existing geographic layers and route rendering."""
import math
import pydeck as pdk
from pydeck.types import String
import streamlit as st
from ui.mission_engine import *
from ui.themes import BASEMAP_STYLES, palette, rgb, theme_name

LABEL_CHARACTERS = String("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- /")

def build_map(mission: dict | None, view: str = "Tactical") -> pdk.Deck:
    mode = theme_name(getattr(st.session_state, "theme", "Light"))
    theme = palette(mode)
    blue, teal, green, gold, red, amber = (rgb(theme[key]) for key in ("blue", "teal", "green", "gold", "red", "amber"))
    layers = []
    zones = [{**zone, "altitude": 160, "color": red + [35], "label": zone["name"]} for zone in RESTRICTED_ZONES]
    layers.append(pdk.Layer("PolygonLayer", zones, id="restriction-volumes", get_polygon="polygon", get_fill_color="color",
                            get_line_color=red + [160], get_elevation="altitude", extruded=view == "Tactical",
                            stroked=True, filled=True, line_width_min_pixels=1, pickable=True))
    selected_id = mission["destination"]["id"] if mission else st.session_state.destination_id
    hospitals = [{"id": hospital.id, "position": [hospital.lng, hospital.lat], "label": hospital.name, "short": hospital.id.replace("HOSP_", "H"),
                  "detail": f"Medical node / {hospital.category}<br>{' / '.join(hospital.capabilities)}<br>Priority {hospital.priority}",
                  "color": gold + [255] if hospital.id == selected_id else red + [210],
                  "radius": 90 if hospital.id == selected_id else 60} for hospital in HOSPITALS]
    bases = [{"position": [base.lng, base.lat], "label": base.name, "short": base.sector,
              "detail": f"Sector {base.sector}<br>{sum(row['status'] in AVAILABLE_STATUSES for row in st.session_state.fleet if row['base_id'] == base.id)} available aircraft",
              "color": green + [230]} for base in BASES]
    layers.append(pdk.Layer("ScatterplotLayer", hospitals, id="hospital-nodes", get_position="position", get_fill_color="color", get_radius="radius", radius_min_pixels=3, pickable=True))
    layers.append(pdk.Layer("ScatterplotLayer", bases, id="base-nodes", get_position="position", get_fill_color="color", get_radius=90, radius_min_pixels=5, pickable=True))
    # Keep all nodes pickable, but label only the destination and hubs in the overview.
    network_labels = [row for row in hospitals if row["id"] == selected_id] + bases
    layers.append(pdk.Layer("TextLayer", network_labels, id="network-labels", get_position="position", get_text="short", get_color="color", get_size=11, get_pixel_offset=[0, -17], font_family=String("Arial"), character_set=LABEL_CHARACTERS, get_text_anchor=String("middle")))
    fleet_markers = []
    for index, drone in enumerate(st.session_state.fleet):
        if mission and mission["aircraft"] and drone["id"] == mission["aircraft"]["id"]:
            continue
        base = BASE_BY_ID[drone["base_id"]]
        offset = (index % 3 - 1) * 0.0014
        fleet_markers.append({"position": [base.lng + offset, base.lat + 0.0015, 25 if drone["status"] == "ACTIVE" else 0],
                              "label": drone["id"], "detail": f"{drone['model']}<br>{drone['status']} / battery {drone['battery_pct']:.0f}% / capacity {drone['max_payload_kg']:g} kg",
                              "color": blue + [240] if drone["status"] == "ACTIVE" else green + [160] if drone["status"] in AVAILABLE_STATUSES else gold + [160]})
    layers.append(pdk.Layer("ScatterplotLayer", fleet_markers, id="network-aircraft", get_position="position", get_radius=30, get_fill_color="color", radius_min_pixels=2, pickable=True))
    if mission and mission["route"]["path"]:
        path = mission["route"]["path"]
        hazard = mission["route"]["hazard"]
        if hazard:
            center = to_xy(hazard["position"])
            ring = [to_geo((center[0] + math.cos(angle * math.pi / 24) * hazard["radius_km"], center[1] + math.sin(angle * math.pi / 24) * hazard["radius_km"])) for angle in range(48)]
            layers.append(pdk.Layer("PolygonLayer", [{"polygon": ring, "label": "Dynamic obstacle interference"}], id="dynamic-hazard", get_polygon="polygon", get_fill_color=amber + [65], get_line_color=amber + [230], get_elevation=130, extruded=view == "Tactical", line_width_min_pixels=2, stroked=True, pickable=True))
        color = blue if mission["safety"]["clearance"] else red
        layers.append(pdk.Layer("PathLayer", [{"path": path, "label": "Planned flight corridor"}], id="route-halo", get_path="path", get_color=color + [46], width_min_pixels=10, width_max_pixels=10))
        layers.append(pdk.Layer("PathLayer", [{"path": path, "label": "Planned flight corridor"}], id="flight-corridor", get_path="path", get_color=color + [230], width_min_pixels=2, pickable=True))
        waypoints = []
        geometric = [[point[0], point[1]] for point in [path[int((len(path) - 1) * fraction)] for fraction in (0, 0.2, 0.4, 0.6, 0.85, 1)]]
        for index, position in enumerate(geometric):
            label = "LAUNCH" if index == 0 else "DESTINATION" if index == len(geometric) - 1 else "APPROACH" if index == len(geometric) - 2 else f"WP-{index:02d}"
            waypoints.append({"position": [*position, 0 if index in {0, len(geometric) - 1} else 110], "label": label,
                              "detail": f"{'Departure' if index == 0 else 'Approach' if index == len(geometric) - 1 else 'Cruise waypoint'}<br>{position[1]:.4f} N / {position[0]:.4f} E<br>{haversine(position, geometric[-1]):.2f} km to destination"})
        layers.append(pdk.Layer("ScatterplotLayer", waypoints, id="route-waypoints", get_position="position", get_radius=32, get_fill_color=teal + [250], radius_min_pixels=3, pickable=True))
        waypoint_labels = [waypoints[0], waypoints[len(waypoints) // 2], waypoints[-1]]
        layers.append(pdk.Layer("TextLayer", waypoint_labels, id="waypoint-labels", get_position="position", get_text="label", get_color=teal, get_size=10, get_pixel_offset=[0, 16], font_family=String("Arial"), character_set=LABEL_CHARACTERS))
        if mission["safety"]["clearance"]:
            point = flight_position(mission)
            completed = path[:max(1, int(mission["progress"] * (len(path) - 1)) + 1)]
            returning = mission["status"] in {"RETURNING", "DELIVERED", "ABORTED"} and mission["elapsed"] > 0
            outbound_tip = mission["return_path"][0] if returning else point
            layers.append(pdk.Layer("PathLayer", [{"path": completed + [outbound_tip]}], id="executed-flight", get_path="path", get_color=green + [240], width_min_pixels=3))
            if returning:
                return_path = mission["return_path"]
                flown_return = return_path[:max(1, int(mission["return_progress"] * (len(return_path) - 1)) + 1)] + [point]
                layers.append(pdk.Layer("PathLayer", [{"path": flown_return}], id="return-flight", get_path="path", get_color=teal + [200], width_min_pixels=2))
            layers.append(pdk.Layer("ScatterplotLayer", [{"position": point, "label": mission["aircraft"]["id"]}], id="live-aircraft", get_position="position", get_radius=75, get_fill_color=blue + [255], stroked=True, get_line_color=rgb(theme["surface"]), line_width_min_pixels=2, radius_min_pixels=7, pickable=True))
            layers.append(pdk.Layer("TextLayer", [{"position": point, "label": mission["aircraft"]["id"]}], id="aircraft-call-sign", get_position="position", get_text="label", get_color=blue, get_size=12, get_pixel_offset=[0, -36], font_family=String("Arial"), character_set=LABEL_CHARACTERS))
    lat, lng, zoom = 16.495, 80.615, 10.9
    if mission and mission["aircraft"]:
        base = BASE_BY_ID[mission["aircraft"]["base_id"]]
        lat = (base.lat + mission["destination"]["lat"]) / 2
        lng = (base.lng + mission["destination"]["lng"]) / 2
        zoom = 12.0 if mission["route"]["distance_km"] < 5 else 11.4
    return pdk.Deck(layers=layers, map_provider="carto", map_style=BASEMAP_STYLES[mode],
                    initial_view_state=pdk.ViewState(latitude=lat, longitude=lng, zoom=zoom, pitch=48 if view == "Tactical" else 0, bearing=-12 if view == "Tactical" else 0),
                    tooltip={"html": "<b>{label}</b><br>{detail}", "style": {"backgroundColor": theme["surface"], "color": theme["text"], "fontSize": "11px"}},
                    height=570)

