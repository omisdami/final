from fastapi import APIRouter, HTTPException, Body, Query
from pathlib import Path
import json, os, re
from jsonschema import validate, ValidationError



router = APIRouter()

# Your current structure keeps JSON in the same templates/ folder
TEMPLATES_DIR = Path("templates").resolve()
SCHEMA_PATH   = TEMPLATES_DIR / "template_schema.json"

with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    TEMPLATE_SCHEMA = json.load(f)

SAFE = re.compile(r"^[A-Za-z0-9._-]+$")

def safe_name(name: str) -> str:
    if not SAFE.fullmatch(name):
        raise HTTPException(400, "Invalid template name")
    return name if name.endswith(".json") else f"{name}.json"

@router.get("/api/templates")
def list_templates():
    return sorted([p.name for p in TEMPLATES_DIR.glob("*.json")])

@router.get("/api/templates/{name}")
def get_template(name: str):
    p = TEMPLATES_DIR / safe_name(name)
    if not p.exists(): raise HTTPException(404, "Not found")
    return json.loads(p.read_text(encoding="utf-8"))

@router.post("/api/templates")
def create_template(name: str = Query(...), body: dict = Body(...)):
    fname = safe_name(name)
    try: validate(body, TEMPLATE_SCHEMA)
    except ValidationError as e: raise HTTPException(400, f"Schema error: {e.message}")
    tmp = TEMPLATES_DIR / (fname + ".tmp")
    out = TEMPLATES_DIR / fname
    tmp.write_text(json.dumps(body, indent=2), encoding="utf-8")
    os.replace(tmp, out)
    return {"ok": True, "name": fname}

@router.put("/api/templates/{name}")
def update_template(name: str, body: dict = Body(...)):
    p = TEMPLATES_DIR / safe_name(name)
    if not p.exists(): raise HTTPException(404, "Not found")
    try: validate(body, TEMPLATE_SCHEMA)
    except ValidationError as e: raise HTTPException(400, f"Schema error: {e.message}")
    tmp = Path(str(p) + ".tmp")
    tmp.write_text(json.dumps(body, indent=2), encoding="utf-8")
    os.replace(tmp, p)
    return {"ok": True}

@router.delete("/api/templates/{name}")
def delete_template(name: str):
    p = TEMPLATES_DIR / safe_name(name)
    if not p.exists(): raise HTTPException(404, "Not found")
    p.unlink()
    return {"ok": True}
