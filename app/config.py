import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    database_path: Path
    admin_password_hash: str
    session_secret: str
    cookie_secure: bool
    catalog_path: Path


def load_settings() -> Settings:
    load_dotenv(ROOT / ".env")
    password_hash = os.getenv("ADMIN_PASSWORD_HASH", "")
    session_secret = os.getenv("SESSION_SECRET", "")
    missing = [name for name, value in (("ADMIN_PASSWORD_HASH", password_hash), ("SESSION_SECRET", session_secret)) if not value or "replace" in value]
    if missing:
        raise RuntimeError("Configuración incompleta: defina " + ", ".join(missing) + " en .env.")
    database_path = Path(os.getenv("DATABASE_PATH", "data/nodos.sqlite3"))
    if not database_path.is_absolute():
        database_path = ROOT / database_path
    return Settings(database_path, password_hash, session_secret, os.getenv("COOKIE_SECURE", "false").lower() == "true", ROOT / "catalog.yml")


def load_catalog(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as fh:
            catalog = yaml.safe_load(fh)
    except (OSError, yaml.YAMLError) as exc:
        raise RuntimeError(f"No se pudo leer el catálogo YAML: {exc}") from exc
    if not isinstance(catalog, dict) or not all(isinstance(catalog.get(key), list) and catalog[key] for key in ("nodes", "days", "slots")):
        raise RuntimeError("Catálogo inválido: se requieren listas no vacías nodes, days y slots.")
    for kind in ("nodes", "days", "slots"):
        values = catalog[kind]
        if any(not isinstance(item, dict) or not item.get("id") for item in values):
            raise RuntimeError(f"Catálogo inválido: cada elemento de {kind} requiere un id.")
        ids = [item["id"] for item in values]
        if len(ids) != len(set(ids)):
            raise RuntimeError(f"Catálogo inválido: IDs duplicados en {kind}.")
    if any(not item.get("name") for item in catalog["nodes"]):
        raise RuntimeError("Catálogo inválido: cada nodo requiere name.")
    return catalog
