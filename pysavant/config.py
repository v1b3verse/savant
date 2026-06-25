"""House configuration discovery — download and parse uiconfig.tar.gz.

Provides:
- ConfigDownloader: downloads uiconfig.tar.gz over the WebSocket
- ConfigParser: reads serviceImplementation.sqlite into Python models
- HouseConfig: structured access to rooms, services, and entities
"""

from __future__ import annotations

import io
import logging
import sqlite3
import tarfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ── Models ──────────────────────────────────────────────────────────────────


@dataclass
class LightEntity:
    zone_id: int
    name: str
    addresses: str
    state_name: str
    entity_type: str = ""
    technology: str = ""
    is_dimmer: bool = False
    is_sceneable: bool = False


@dataclass
class ShadeEntity:
    zone_id: int
    name: str
    addresses: str
    state_name: str = ""


@dataclass
class HVACEntity:
    zone_id: int
    name: str
    addresses: str
    state_name: str = ""
    has_heat: bool = False
    has_cool: bool = False
    has_auto: bool = False
    is_celsius: bool = True
    temp_min: float = 5.0
    temp_max: float = 40.0


@dataclass
class FanEntity:
    zone_id: int
    name: str
    addresses: str
    state_name: str = ""


@dataclass
class GarageEntity:
    name: str
    addresses: str
    open_command: str = ""
    close_command: str = ""


@dataclass
class SecurityEntity:
    zone_id: int
    name: str
    state_name: str = ""
    partition_number: int = 0
    zone_number: int = 0


@dataclass
class ZoneService:
    """A service (lighting, HVAC, shades …) exposed by a zone."""

    zone_name: str
    component: str
    logical_component: str
    service_type: str
    service_variant_id: str = ""
    service: str = ""


@dataclass
class Room:
    """A room in the house with its capabilities and entities."""

    room_id: str  # UUID
    name: str
    display_name: str
    group: str = ""
    allows_independent_services: bool = True

    # Capabilities
    has_lights: bool = False
    has_shades: bool = False
    has_hvac: bool = False
    has_security: bool = False
    has_fans: bool = False
    has_cameras: bool = False
    has_av: bool = False

    # Entities keyed by zone name
    lights: list[LightEntity] = field(default_factory=list)
    shades: list[ShadeEntity] = field(default_factory=list)
    hvac: list[HVACEntity] = field(default_factory=list)
    fans: list[FanEntity] = field(default_factory=list)
    security: list[SecurityEntity] = field(default_factory=list)


@dataclass
class InfrastructureDevice:
    """A non-room device (pump, valve, fan, relay, etc.) in a hidden zone.

    These are modeled as LightEntity rows in the SQLite but are actually
    infrastructure — water pumps, gas valves, ventilation relays, towel
    warmers, radiant floor heating, spare relays, etc.
    """

    name: str
    state_name: str
    address: str = ""
    is_dimmer: bool = False
    category: str = "other"  # pump, valve, fan, heating, towel, garage, relay, other
    zone: str = ""


@dataclass
class HouseConfig:
    """Complete house configuration from the SQLite database."""

    rooms: list[Room] = field(default_factory=list)
    zones: list[ZoneService] = field(default_factory=list)
    infrastructure: list[InfrastructureDevice] = field(default_factory=list)
    raw_tables: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    # Convenience accessors
    _room_by_id: dict[str, Room] = field(default_factory=dict)
    _room_by_name: dict[str, Room] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._room_by_id = {r.room_id: r for r in self.rooms}
        self._room_by_name = {r.name: r for r in self.rooms}

    def get_room(self, name: str | None = None, room_id: str | None = None) -> Room | None:
        if room_id:
            return self._room_by_id.get(room_id)
        if name:
            return self._room_by_name.get(name)
        return None


# ── SQLite parser ───────────────────────────────────────────────────────────


class ConfigParser:
    """Reads serviceImplementation.sqlite and builds a HouseConfig."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        """
        Args:
            db_path: Path to the SQLite file on disk. If None, use
                     ``from_connection()`` instead.
        """
        self._db_path = Path(db_path) if db_path else None
        self._conn: sqlite3.Connection | None = None

    @classmethod
    def from_connection(cls, conn: sqlite3.Connection) -> ConfigParser:
        """Create a parser from an already-open connection (e.g. in-memory)."""
        parser = cls()
        parser._conn = conn
        return parser

    def parse(self) -> HouseConfig:
        if self._conn is None and self._db_path is not None:
            self._conn = sqlite3.connect(str(self._db_path))
            self._conn.row_factory = sqlite3.Row
        elif self._conn is not None:
            self._conn.row_factory = sqlite3.Row
        else:
            raise RuntimeError("No database path or connection provided")

        try:
            rooms = self._parse_rooms()
            zones = self._parse_zone_services()
            infrastructure = self._parse_infrastructure()
            raw_tables = self._collect_raw_tables()
            return HouseConfig(
                rooms=rooms,
                zones=zones,
                infrastructure=infrastructure,
                raw_tables=raw_tables,
            )
        finally:
            if self._db_path is not None:
                self._conn.close()
                self._conn = None

    def _cursor(self) -> sqlite3.Cursor:
        assert self._conn is not None
        return self._conn.cursor()

    # ═══════════════════════════════════════════════════════════════════════
    # Rooms
    # ═══════════════════════════════════════════════════════════════════════

    def _parse_rooms(self) -> list[Room]:
        cursor = self._cursor()

        # Rooms
        cursor.execute(
            "SELECT id, name, roomID, allowsIndependentServices, "
            "shown, enabled FROM Rooms ORDER BY name"
        )
        room_rows = {r["name"]: r for r in cursor.fetchall()}

        # RoomCapabilities (uses Rooms.id = integer, not UUID)
        cursor.execute(
            "SELECT rc.*, r.name AS room_name FROM RoomCapabilities rc "
            "JOIN Rooms r ON r.id = rc.roomID"
        )
        caps = {r["room_name"]: dict(r) for r in cursor.fetchall()}

        # RoomGroups
        cursor.execute(
            "SELECT r.name AS roomName, rg.name AS groupName "
            "FROM Rooms r "
            "LEFT JOIN RoomGroupMap rgm ON r.id = rgm.roomID "
            "LEFT JOIN RoomGroups rg ON rgm.groupID = rg.id "
            "ORDER BY r.name"
        )
        group_map = {r["roomName"]: r["groupName"] or "" for r in cursor.fetchall()}

        # Zones -> room mapping via ZoneRoomMap (uses Rooms.id = integer, not Rooms.roomID = UUID)
        cursor.execute(
            "SELECT z.id AS zid, z.name AS zname, zrm.roomID AS rid "
            "FROM Zones z "
            "JOIN ZoneRoomMap zrm ON zrm.zoneID = z.id"
        )
        zones_by_room: dict[int, list[int]] = {}
        for r in cursor.fetchall():
            zid = r["zid"]
            rid = r["rid"]
            if rid not in zones_by_room:
                zones_by_room[rid] = []
            zones_by_room[rid].append(zid)

        rooms: list[Room] = []
        for room_name, row in room_rows.items():
            if not row["shown"]:
                continue

            room_uuid = row["roomID"]
            room_int_id = row["id"]
            cap = caps.get(room_name, {})

            room = Room(
                room_id=room_uuid or str(room_int_id),
                name=room_name.strip(),
                display_name=room_name.strip(),
                group=group_map.get(room_name, ""),
                allows_independent_services=bool(row["allowsIndependentServices"]),
                has_lights=bool(cap.get("hasLights", False)),
                has_shades=bool(cap.get("hasShades", False)),
                has_hvac=bool(cap.get("hasHVAC", False)),
                has_security=bool(cap.get("hasSecurity", False)),
                has_fans=bool(cap.get("hasFans", False)),
                has_cameras=bool(cap.get("hasCameras", False)),
                has_av=bool(cap.get("hasAV", False)),
            )

            # Populate entities for this room
            zone_ids = zones_by_room.get(room_int_id, [])
            for zid in zone_ids:
                room.lights.extend(self._parse_lights_for_zone(zid))
                room.shades.extend(self._parse_shades_for_zone(zid))
                room.hvac.extend(self._parse_hvac_for_zone(zid))
                room.fans.extend(self._parse_fans_for_zone(zid))
                room.security.extend(self._parse_security_for_zone(zid))

            rooms.append(room)

        return rooms

    # ═══════════════════════════════════════════════════════════════════════
    # Zone services
    # ═══════════════════════════════════════════════════════════════════════

    def _parse_zone_services(self) -> list[ZoneService]:
        cursor = self._cursor()
        try:
            cursor.execute(
                "SELECT DISTINCT zone, component, logicalComponent, "
                "serviceType, serviceVariantID, service "
                "FROM ServiceImplementationServiceResources "
                "ORDER BY zone, component"
            )
            return [
                ZoneService(
                    zone_name=r["zone"],
                    component=r["component"],
                    logical_component=r["logicalComponent"] or "",
                    service_type=r["serviceType"] or "",
                    service_variant_id=r["serviceVariantID"] or "",
                    service=r["service"] or "",
                )
                for r in cursor.fetchall()
            ]
        except sqlite3.OperationalError:
            logger.warning("ServiceImplementationServiceResources table not available")
            return []

    # ═══════════════════════════════════════════════════════════════════════
    # Entity parsers
    # ═══════════════════════════════════════════════════════════════════════

    def _parse_lights_for_zone(self, zone_id: int) -> list[LightEntity]:
        cursor = self._cursor()
        cursor.execute(
            "SELECT name, addresses, stateName, entityType, technology, "
            "dimmerCommand, isSceneable "
            "FROM LightEntities WHERE zoneID=? ORDER BY id",
            (zone_id,),
        )
        return [
            LightEntity(
                zone_id=zone_id,
                name=r["name"],
                addresses=r["addresses"] or "",
                state_name=r["stateName"] or "",
                entity_type=r["entityType"] or "",
                technology=r["technology"] or "",
                is_dimmer=bool(r["dimmerCommand"]),
                is_sceneable=bool(r["isSceneable"]),
            )
            for r in cursor.fetchall()
        ]

    def _parse_shades_for_zone(self, zone_id: int) -> list[ShadeEntity]:
        cursor = self._cursor()
        cursor.execute(
            "SELECT name, addresses, stateName FROM ShadeEntities WHERE zoneID=? ORDER BY id",
            (zone_id,),
        )
        return [
            ShadeEntity(
                zone_id=zone_id,
                name=r["name"],
                addresses=r["addresses"] or "",
                state_name=r["stateName"] or "",
            )
            for r in cursor.fetchall()
        ]

    def _parse_hvac_for_zone(self, zone_id: int) -> list[HVACEntity]:
        cursor = self._cursor()
        try:
            cursor.execute(
                "SELECT name, addresses, stateName, heat, cool, auto, "
                "isCelsius, tempMinRange, tempMaxRange "
                "FROM HVACEntities WHERE zoneID=? ORDER BY id",
                (zone_id,),
            )
            return [
                HVACEntity(
                    zone_id=zone_id,
                    name=r["name"],
                    addresses=str(r["addresses"] or ""),
                    state_name=r["stateName"] or "",
                    has_heat=bool(r["heat"]),
                    has_cool=bool(r["cool"]),
                    has_auto=bool(r["auto"]) if r["auto"] is not None else False,
                    is_celsius=bool(r["isCelsius"]) if r["isCelsius"] is not None else True,
                    temp_min=float(r["tempMinRange"] or 5.0) if r["tempMinRange"] else 5.0,
                    temp_max=float(r["tempMaxRange"] or 40.0) if r["tempMaxRange"] else 40.0,
                )
                for r in cursor.fetchall()
            ]
        except sqlite3.OperationalError:
            return []

    def _parse_fans_for_zone(self, zone_id: int) -> list[FanEntity]:
        cursor = self._cursor()
        cursor.execute(
            "SELECT name, addresses, stateName FROM FanEntities WHERE zoneID=? ORDER BY id",
            (zone_id,),
        )
        return [
            FanEntity(
                zone_id=zone_id,
                name=r["name"],
                addresses=r["addresses"] or "",
                state_name=r["stateName"] or "",
            )
            for r in cursor.fetchall()
        ]

    def _parse_security_for_zone(self, zone_id: int) -> list[SecurityEntity]:
        cursor = self._cursor()
        try:
            cursor.execute(
                "SELECT name, partitionNumber, zoneNumber, statusState "
                "FROM SecuritySystemEntities WHERE zoneID=? ORDER BY id",
                (zone_id,),
            )
            return [
                SecurityEntity(
                    zone_id=zone_id,
                    name=r["name"],
                    state_name=r["statusState"] or "",
                    partition_number=r["partitionNumber"] or 0,
                    zone_number=r["zoneNumber"] or 0,
                )
                for r in cursor.fetchall()
            ]
        except sqlite3.OperationalError:
            return []

    # ═══════════════════════════════════════════════════════════════════════
    # Raw table dumps (for debugging / completeness)
    # ═══════════════════════════════════════════════════════════════════════

    def _collect_raw_tables(self) -> dict[str, list[dict[str, Any]]]:
        cursor = self._cursor()
        tables: dict[str, list[dict[str, Any]]] = {}
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        for (tbl,) in cursor.fetchall():
            try:
                cursor.execute(f"SELECT * FROM [{tbl}]")
                tables[tbl] = [dict(r) for r in cursor.fetchall()]
            except sqlite3.OperationalError:
                pass
        return tables

    # ═══════════════════════════════════════════════════════════════════════
    # Infrastructure devices (hidden zones: pumps, valves, relays, etc.)
    # ═══════════════════════════════════════════════════════════════════════

    def _parse_infrastructure(self) -> list[InfrastructureDevice]:
        """Collect non-room devices from hidden zones (HIDDEN, Home, etc.).

        These are LightEntity rows whose zone isn't linked to a visible room.
        They represent pumps, valves, ventilation relays, towel warmers,
        radiant floor heating, spare relays, and similar infrastructure.
        """
        cursor = self._cursor()

        # Find hidden zone IDs — zones NOT linked to a shown room
        cursor.execute(
            "SELECT DISTINCT z.id, z.name FROM Zones z "
            "LEFT JOIN ZoneRoomMap zrm ON zrm.zoneID = z.id "
            "LEFT JOIN Rooms r ON r.id = zrm.roomID "
            "WHERE r.id IS NULL OR r.shown = 0 "
            "ORDER BY z.name"
        )
        hidden_zone_ids = [r["id"] for r in cursor.fetchall()]

        if not hidden_zone_ids:
            return []

        placeholders = ",".join("?" for _ in hidden_zone_ids)

        cursor.execute(
            f"SELECT l.name, l.stateName, l.addresses, l.dimmerCommand, "
            f"z.name AS zone_name "
            f"FROM LightEntities l "
            f"JOIN Zones z ON z.id = l.zoneID "
            f"WHERE l.zoneID IN ({placeholders}) "
            f"ORDER BY l.name",
            hidden_zone_ids,
        )

        devices: list[InfrastructureDevice] = []
        for r in cursor.fetchall():
            name = r["name"]
            state = r["stateName"] or ""
            addr_raw = r["addresses"] or ""
            addr = addr_raw.split(",")[0] if addr_raw else ""
            is_dimmer = bool(r["dimmerCommand"])
            zone = r["zone_name"]

            category = self._classify_infrastructure(name)
            devices.append(
                InfrastructureDevice(
                    name=name,
                    state_name=state,
                    address=addr,
                    is_dimmer=is_dimmer,
                    category=category,
                    zone=zone,
                )
            )

        return devices

    @staticmethod
    def _classify_infrastructure(name: str) -> str:
        name_lower = name.lower()
        if "bomba" in name_lower or "bomb" in name_lower:
            return "pump"
        if "eval" in name_lower and ("agua" in name_lower or "gas" in name_lower):
            return "valve"
        if "vex" in name_lower or ("vent" in name_lower and "ventax" not in name_lower):
            return "fan"
        if "ehf" in name_lower or "piso radiante" in name_lower:
            return "heating"
        if "tw" in name_lower or "toalheiro" in name_lower or "towel" in name_lower:
            return "towel"
        if "garagem" in name_lower or "portao" in name_lower or "garage" in name_lower:
            return "garage"
        if "hc switch" in name_lower or "switchover" in name_lower:
            return "hvac_switch"
        if "reserva" in name_lower:
            return "relay"
        return "other"


# ── Binary transfer protocol ────────────────────────────────────────────────


HEADER_SIZE = 14


class BinaryTransferReceiver:
    """Reassembles a file from binary TransferPacket chunks.

    Wire format (14-byte header + ident/options + payload):
      [0]      type       (1=file)
      [1]      flags      (bit7=isComplete, bits0-6=version)
      [2-9]    fileSize   (big-endian uint64)
      [10-13]  identLen   (big-endian uint32)
      [14+]    ident/options | payload
    """

    def __init__(self) -> None:
        self._file_data = bytearray()
        self._expected_size = 0
        self._identifier = ""
        self._complete = False

    @property
    def complete(self) -> bool:
        return self._complete

    @property
    def file_size(self) -> int:
        return self._expected_size

    @property
    def data(self) -> bytes:
        return bytes(self._file_data)

    def feed(self, frame: bytes) -> bool:
        """Process one binary frame. Returns True when the transfer is complete."""
        if len(frame) < HEADER_SIZE:
            logger.warning("Binary frame too short: %d bytes", len(frame))
            return False

        flags = frame[1]
        is_complete = bool(flags & 0x80)
        file_size = int.from_bytes(frame[2:10], "big")
        ident_len = int.from_bytes(frame[10:14], "big")

        if ident_len > 0:
            self._identifier = frame[14 : 14 + ident_len].decode(
                "latin-1", errors="replace"
            )

        payload_start = HEADER_SIZE + ident_len
        if payload_start < len(frame):
            self._file_data.extend(frame[payload_start:])

        self._expected_size = file_size

        if is_complete:
            self._complete = True
            return True

        return False


# ── Top-level download + parse helper ───────────────────────────────────────


async def download_and_parse_config(client: Any) -> HouseConfig:
    """One-shot: download uiconfig.tar.gz from the connected client and parse it.

    ``client`` must be a connected ``SavantClient`` instance.

    The archive is kept in memory. The SQLite database is extracted to a
    single temp file which is deleted after parsing.
    """
    raw = await client.download_config_archive("uiconfig.tar.gz")

    # Open tar.gz from memory
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tar:
        # Find and extract serviceImplementation.sqlite in memory
        db_member = None
        for m in tar.getmembers():
            if m.name.endswith("serviceImplementation.sqlite"):
                db_member = m
                break

        if db_member is None:
            raise FileNotFoundError(
                "serviceImplementation.sqlite not found in archive"
            )

        src = tar.extractfile(db_member)
        if src is None:
            raise FileNotFoundError(
                f"Could not extract {db_member.name} from archive"
            )
        db_bytes = src.read()

    # Load into an in-memory SQLite database via deserialize (Python 3.7+)
    mem_conn = sqlite3.connect(":memory:")
    try:
        mem_conn.deserialize(db_bytes)
        parser = ConfigParser.from_connection(mem_conn)
        return parser.parse()
    finally:
        mem_conn.close()
