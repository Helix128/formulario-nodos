from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
import re

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from .config import ROOT, load_catalog, load_settings
from .database import Response, ResponseSlot, make_session_factory

EMAIL = re.compile(r"^[^\s@]+@udd\.cl$", re.I)


class Submission(BaseModel):
    name: str = Field(min_length=3, max_length=250)
    email: str = Field(max_length=320)
    preference_1: str
    preference_2: str
    additional_idea: str = Field(default="", max_length=5000)
    busy_slots: list[dict]
    replace_existing: bool = False


def create_app(settings=None, catalog=None, session_factory=None) -> FastAPI:
    settings = settings or load_settings()
    catalog = catalog or load_catalog(settings.catalog_path)
    session_factory = session_factory or make_session_factory(settings.database_path)[0]
    nodes = {node["id"]: node for node in catalog["nodes"]}
    day_ids = {day["id"] for day in catalog["days"]}
    slot_ids = {slot["id"] for slot in catalog["slots"]}

    @asynccontextmanager
    async def lifespan(app):
        yield

    app = FastAPI(title="Formulario NODO", lifespan=lifespan)
    app.add_middleware(SessionMiddleware, secret_key=settings.session_secret, https_only=settings.cookie_secure, same_site="lax")
    app.mount("/static", StaticFiles(directory=ROOT / "app/static"), name="static")
    templates = Jinja2Templates(directory=ROOT / "app/templates")
    app.state.catalog, app.state.session_factory = catalog, session_factory
    hasher = PasswordHasher()

    def admin(request: Request):
        if not request.session.get("admin"):
            raise HTTPException(status_code=401, detail="Autenticación requerida")

    @app.get("/", response_class=HTMLResponse)
    def form(request: Request):
        return templates.TemplateResponse(request, "form.html", {"catalog": catalog})

    @app.post("/api/responses")
    def save_response(payload: Submission):
        name, email = payload.name.strip(), payload.email.strip().lower()
        if len(name) < 3 or not EMAIL.fullmatch(email):
            raise HTTPException(422, "Nombre o correo institucional inválido.")
        if payload.preference_1 == payload.preference_2 or payload.preference_1 not in nodes or payload.preference_2 not in nodes:
            raise HTTPException(422, "Seleccione dos Nodos vigentes y distintos.")
        pairs = {(item.get("day_id"), item.get("slot_id")) for item in payload.busy_slots}
        if any(day not in day_ids or slot not in slot_ids for day, slot in pairs):
            raise HTTPException(422, "La disponibilidad contiene un bloque que no existe en el catálogo.")
        with session_factory.begin() as db:
            response = db.scalar(select(Response).where(Response.email == email))
            if response and not payload.replace_existing:
                return JSONResponse(status_code=409, content={"detail": "Ya existe una respuesta para este correo.", "requires_confirmation": True})
            replaced = response is not None
            if response is None:
                response = Response(email=email, name=name, preference_1=payload.preference_1, preference_2=payload.preference_2, additional_idea=payload.additional_idea.strip())
                db.add(response)
                db.flush()
            else:
                response.name, response.preference_1, response.preference_2 = name, payload.preference_1, payload.preference_2
                response.additional_idea, response.updated_at = payload.additional_idea.strip(), datetime.utcnow()
                response.slots.clear()
                db.flush()
            # Store the full matrix (not only busy cells), so every submitted
            # response has a complete, auditable 5×9 availability record.
            response.slots = [
                ResponseSlot(day_id=day, slot_id=slot, busy=(day, slot) in pairs)
                for day in day_ids for slot in slot_ids
            ]
        return {"ok": True, "replaced": replaced}

    @app.get("/admin/login", response_class=HTMLResponse)
    def login_page(request: Request):
        if request.session.get("admin"):
            return RedirectResponse("/admin", 303)
        return templates.TemplateResponse(request, "login.html", {})

    @app.post("/admin/login")
    async def login(request: Request):
        form_data = await request.form()
        try:
            valid = hasher.verify(settings.admin_password_hash, form_data.get("password", ""))
        except VerifyMismatchError:
            valid = False
        if not valid:
            return templates.TemplateResponse(request, "login.html", {"error": "Contraseña incorrecta."}, status_code=401)
        request.session["admin"] = True
        return RedirectResponse("/admin", 303)

    @app.post("/admin/logout")
    def logout(request: Request):
        request.session.clear()
        return RedirectResponse("/admin/login", 303)

    @app.get("/admin", response_class=HTMLResponse)
    def dashboard(request: Request):
        admin(request)
        return templates.TemplateResponse(request, "admin.html", {"catalog": catalog})

    @app.get("/api/admin/summary")
    def summary(request: Request):
        admin(request)
        with session_factory() as db:
            total = db.scalar(select(func.count()).select_from(Response)) or 0
            pref1 = dict(db.execute(select(Response.preference_1, func.count()).group_by(Response.preference_1)).all())
            pref2 = dict(db.execute(select(Response.preference_2, func.count()).group_by(Response.preference_2)).all())
        return {"total": total, "preference_1": pref1, "preference_2": pref2}

    @app.get("/api/admin/heatmap")
    def heatmap(request: Request, node_id: str | None = None, preference: int | None = None, metric: str = "availability"):
        admin(request)
        if node_id and node_id not in nodes: raise HTTPException(422, "Nodo inválido")
        if preference not in (None, 1, 2): raise HTTPException(422, "Preferencia inválida")
        if metric not in ("availability", "occupancy"): raise HTTPException(422, "Métrica inválida")
        with session_factory() as db:
            stmt = select(Response)
            if node_id:
                if preference == 1: stmt = stmt.where(Response.preference_1 == node_id)
                elif preference == 2: stmt = stmt.where(Response.preference_2 == node_id)
                else: stmt = stmt.where((Response.preference_1 == node_id) | (Response.preference_2 == node_id))
            responses = db.scalars(stmt).all()
            total = len(responses)
            busy = {(slot.response_id, slot.day_id, slot.slot_id) for slot in db.scalars(select(ResponseSlot).where(ResponseSlot.response_id.in_([r.id for r in responses] or [-1])).where(ResponseSlot.busy.is_(True))) }
        cells = []
        for slot in catalog["slots"]:
            for day in catalog["days"]:
                occupied = sum((response.id, day["id"], slot["id"]) in busy for response in responses)
                count = occupied if metric == "occupancy" else total - occupied
                cells.append({"day_id": day["id"], "slot_id": slot["id"], "count": count, "percent": round((count / total * 100) if total else 0, 1)})
        return {"total": total, "metric": metric, "cells": cells}

    @app.get("/api/admin/responses")
    def response_details(request: Request):
        admin(request)
        with session_factory() as db:
            entries = db.scalars(select(Response).order_by(Response.created_at.desc())).all()
            all_slots = db.scalars(select(ResponseSlot)).all()
        busy_by_response = {}
        for item in all_slots:
            if item.busy:
                busy_by_response.setdefault(item.response_id, set()).add(f"{item.day_id}:{item.slot_id}")
        return [{"id": r.id, "name": r.name, "email": r.email, "preference_1": r.preference_1, "preference_2": r.preference_2, "additional_idea": r.additional_idea, "created_at": r.created_at.isoformat(), "busy_slots": list(busy_by_response.get(r.id, set()))} for r in entries]

    return app


app = create_app()
