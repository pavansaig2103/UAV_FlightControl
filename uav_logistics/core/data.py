"""Unchanged city network, aircraft profiles and mission data types."""
from dataclasses import asdict, dataclass
from pathlib import Path
from uav_logistics.ui.themes import LIGHT

ROOT = Path(__file__).resolve().parents[2]
EARTH_RADIUS_KM = 6371.0088
SIMULATION_SECONDS = 45.0
ACTIVE_STATUSES = {"PREFLIGHT", "IN FLIGHT", "PAUSED", "RETURNING"}
AVAILABLE_STATUSES = {"IDLE", "READY"}
WIND_DIRECTIONS = {"N": 0, "NE": 45, "E": 90, "SE": 135, "S": 180, "SW": 225, "W": 270, "NW": 315}
COLORS = {name: LIGHT[key] for name, key in {"cyan": "teal", "blue": "blue", "green": "green", "gold": "gold", "amber": "amber", "red": "red", "muted": "secondary"}.items()}


@dataclass(frozen=True)
class Node:
    id: str
    name: str
    lat: float
    lng: float
    category: str = "Medical Center"
    capabilities: tuple[str, ...] = ("Emergency", "General")
    priority: str = "HIGH"
    sector: str = "CENTRAL"

    def medical_record(self) -> dict:
        return dict(id=self.id, name=self.name, latitude=self.lat, longitude=self.lng, category=self.category,
                    capabilities=list(self.capabilities), priority=self.priority, sector=self.sector)


@dataclass(frozen=True)
class Triage:
    payload_weight_kg: float
    urgency: str
    item_type: str
    weight_assumed: bool = False


HOSPITALS = (
    Node("HOSP_01", "New Government General Hospital (New GGH)", 16.5185, 80.6610, "Public Tertiary", ("Trauma", "Emergency", "Blood Bank", "ICU"), "CRITICAL", "NORTH-EAST"),
    Node("HOSP_02", "Old GGH (Hanumanpet)", 16.5123, 80.6234, "Public General", ("Emergency", "General", "Blood Bank"), "HIGH", "CENTRAL-WEST"),
    Node("HOSP_03", "Aster Ramesh Hospitals (Benz Circle)", 16.5012, 80.6432, "Multispecialty", ("Trauma", "Cardiology", "ICU", "Emergency"), "CRITICAL", "CENTRAL-EAST"),
    Node("HOSP_04", "Manipal Hospital (Tadepalle)", 16.4815, 80.6210, "Tertiary Care", ("Transplant", "Critical Care", "Emergency"), "CRITICAL", "SOUTH"),
    Node("HOSP_05", "Ayush Hospital (Governorpet)", 16.5120, 80.6280, "Multispecialty", ("Emergency", "ICU", "General"), "HIGH", "CENTRAL"),
    Node("HOSP_06", "Andhra Hospitals (Suryaraopet)", 16.5085, 80.6355, "Multispecialty", ("Trauma", "Emergency", "Critical Care"), "HIGH", "CENTRAL"),
    Node("HOSP_07", "Kamineni Hospital (Kanuru)", 16.4875, 80.6890, "Tertiary Care", ("Emergency", "ICU", "General"), "HIGH", "SOUTHEAST"),
    Node("HOSP_08", "Capital Hospital (Poranki)", 16.4760, 80.7012, "Multispecialty", ("Emergency", "Cardiology", "General"), "HIGH", "SOUTHEAST"),
    Node("HOSP_09", "INDLAS Hospitals (Suryaraopet)", 16.5070, 80.6330, "Specialty", ("General", "Critical Care"), "MEDIUM", "CENTRAL"),
    Node("HOSP_10", "Union Hospitals (Gayatri Nagar)", 16.4980, 80.6540, "Multispecialty", ("Emergency", "ICU", "General"), "HIGH", "CENTRAL-EAST"),
    Node("HOSP_11", "Sentini Hospitals (Ring Road)", 16.5234, 80.6718, "Multispecialty", ("Emergency", "Cardiology", "Critical Care"), "HIGH", "NORTH-EAST"),
    Node("HOSP_12", "Rainbow Children's Hospital (Currency Nagar)", 16.5167, 80.6768, "Pediatric", ("Pediatrics", "ICU", "Emergency"), "HIGH", "NORTH-EAST"),
    Node("HOSP_13", "Latha Super Speciality Hospital (Suryaraopet)", 16.5101, 80.6338, "Multispecialty", ("General", "Critical Care", "Emergency"), "HIGH", "CENTRAL"),
    Node("HOSP_14", "NRI General Hospital (Chinakakani)", 16.3840, 80.5469, "Teaching Hospital", ("Emergency", "Blood Bank", "ICU", "General"), "HIGH", "SOUTHWEST"),
    Node("HOSP_15", "AIIMS Mangalagiri", 16.4306, 80.5719, "Public Tertiary", ("Emergency", "Critical Care", "General"), "HIGH", "SOUTHWEST"),
    Node("HOSP_16", "Rainbow Children's Clinic (Governorpet)", 16.5109, 80.6287, "Outpatient Clinic", ("Pediatrics", "General"), "MEDIUM", "CENTRAL"),
)
BASES = (
    Node("BASE_WEST", "Gollapudi West", 16.5412, 80.5734, sector="WEST"),
    Node("BASE_NORTH", "Gunadala North", 16.5321, 80.6512, sector="NORTH"),
    Node("BASE_EAST", "Auto Nagar East", 16.4923, 80.6845, sector="EAST"),
    Node("BASE_SOUTH", "Tadepalle South", 16.4712, 80.6123, sector="SOUTH"),
    Node("BASE_SE", "Kanuru Southeast", 16.4822, 80.6775, sector="SOUTHEAST"),
    Node("BASE_NW", "Ibrahimpatnam Northwest", 16.6000, 80.5350, sector="NORTHWEST"),
)
BASE_BY_ID = {base.id: base for base in BASES}
HOSPITAL_BY_ID = {hospital.id: hospital for hospital in HOSPITALS}
FLEET_SPEC = (
    # ID, model, hub, payload, battery, cruise, maximum speed, range, state, role, cold chain, wind limit.
    ("UAV-W1", "Heavy Medical Logistics", "BASE_WEST", 5.0, 91, 48, 66, 36, "READY", "GENERAL", True, 38),
    ("UAV-W2", "Rapid AED Interceptor", "BASE_WEST", 2.0, 88, 72, 88, 24, "IDLE", "AED_RESPONSE", False, 32),
    ("UAV-W3", "Blood Transport UAV", "BASE_WEST", 3.0, 94, 62, 78, 34, "READY", "BLOOD_TRANSPORT", True, 38),
    ("UAV-N1", "Standard Medical Courier", "BASE_NORTH", 3.0, 95, 60, 78, 30, "ACTIVE", "GENERAL", False, 38),
    ("UAV-N2", "Organ Courier", "BASE_NORTH", 4.5, 94, 58, 82, 32, "READY", "ORGAN_TRANSPORT", True, 38),
    ("UAV-N3", "High-Wind Stabilized UAV", "BASE_NORTH", 4.0, 90, 55, 75, 38, "READY", "GENERAL", True, 45),
    ("UAV-E1", "Heavy Medical Logistics", "BASE_EAST", 6.0, 36, 48, 64, 36, "RECHARGING", "GENERAL", True, 38),
    ("UAV-E2", "Rapid AED Interceptor", "BASE_EAST", 1.8, 100, 72, 88, 26, "READY", "AED_RESPONSE", False, 32),
    ("UAV-E3", "Standard Medical Courier", "BASE_EAST", 3.0, 83, 60, 78, 30, "RESERVED", "GENERAL", False, 38),
    ("UAV-S1", "Cold-Chain UAV", "BASE_SOUTH", 3.5, 92, 56, 74, 36, "READY", "COLD_CHAIN", True, 38),
    ("UAV-S2", "Standard Medical Courier", "BASE_SOUTH", 3.0, 78, 60, 78, 32, "IDLE", "GENERAL", False, 38),
    ("UAV-S3", "Organ Courier", "BASE_SOUTH", 5.0, 97, 58, 82, 48, "READY", "ORGAN_TRANSPORT", True, 38),
    ("UAV-SE1", "Heavy Medical Logistics", "BASE_SE", 6.0, 89, 48, 66, 40, "READY", "GENERAL", True, 38),
    ("UAV-SE2", "Rapid AED Interceptor", "BASE_SE", 1.7, 76, 74, 90, 26, "MAINTENANCE", "AED_RESPONSE", False, 32),
    ("UAV-NW1", "Long-Range Medical UAV", "BASE_NW", 4.0, 91, 64, 82, 64, "READY", "GENERAL", True, 42),
    ("UAV-NW2", "Emergency Response UAV", "BASE_NW", 2.5, 88, 68, 86, 48, "IDLE", "EMERGENCY", True, 38),
)
PRESETS = {
    "Custom Input": "",
    "O-Negative Blood Units (Trauma)": "Critical trauma request for 2.0 kg of O-Negative blood units. Immediate emergency delivery required for active transfusion support.",
    "Transplant Organ Container": "Time-critical transplant organ container weighing 4.5 kg requires immediate controlled transport to the receiving surgical team.",
    "AED Defibrillator Courier": "Emergency request for a 1.5 kg AED defibrillator for a severe cardiac trauma case. Immediate delivery required.",
}
STAGES = (("REQUEST INGESTION", "Destination and request"), ("MEDICAL TRIAGE", "Clinical logistics interpretation"),
          ("PAYLOAD CLASSIFICATION", "Mass, urgency and handling"), ("FLEET FILTERING", "Status, capacity, range and reserve"),
          ("CSP OPTIMIZATION", "Transparent weighted suitability"), ("ROUTE GENERATION", "A* waypoint visibility graph"),
          ("WIND CORRECTION", "Bearing and vector performance"), ("RISK ASSESSMENT", "Weighted simulation score"),
          ("SAFETY VERIFICATION", "Hard dispatch constraints"), ("MISSION AUTHORIZATION", "Preflight release"))
RESTRICTED_ZONES = (
    {"name": "Barrage demonstration zone", "polygon": [[80.5942, 16.5070], [80.6025, 16.5118], [80.6110, 16.5054], [80.6042, 16.4988]]},
    {"name": "Airport demonstration zone", "polygon": [[80.7620, 16.5255], [80.7950, 16.5420], [80.8350, 16.5200], [80.8020, 16.4920]]},
)



def fresh_fleet() -> list[dict]:
    return [dict(id=id_, model=model, base_id=base, payload_capacity_kg=capacity, max_payload_kg=capacity,
                 battery_pct=float(battery), nominal_speed_kmph=speed, max_speed_kmph=maximum, range_km=range_,
                 status=state, medical_role=role, cold_chain=cold, max_wind_kmph=limit)
            for id_, model, base, capacity, battery, speed, maximum, range_, state, role, cold, limit in FLEET_SPEC]



def get_hospitals() -> list[dict]:
    return [hospital.medical_record() for hospital in HOSPITALS]

