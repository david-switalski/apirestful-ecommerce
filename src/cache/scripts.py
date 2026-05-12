# src/cache/scripts.py
from pathlib import Path

# Resuelve la ruta absoluta del directorio actual (src/cache)
CURRENT_DIR = Path(__file__).resolve().parent
LUA_DIR = CURRENT_DIR / "lua"


def _load_lua_script(filename: str) -> str:
    """Lee un archivo Lua del disco y lo retorna como string."""
    filepath = LUA_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Lua script not found: {filepath}")

    with open(filepath, encoding="utf-8") as f:
        return f.read()


# Estas variables se inicializan una sola vez al arrancar FastAPI
DEDUCT_STOCK_SCRIPT = _load_lua_script("deduct_stock.lua")
ROLLBACK_STOCK_SCRIPT = _load_lua_script("rollback_stock.lua")
