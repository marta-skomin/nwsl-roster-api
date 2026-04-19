
from fastapi import FastAPI, HTTPException, Query, Depends, Request
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from typing import Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.models import Player, PlayerUpdate, SquadStats
from app.database import create_tables, get_db, SessionLocal
from app.data import (
    load_rosters, get_team_players, get_player,
    get_player_by_name, get_player_row,
    insert_player, update_player_row, list_teams
)
from app.kafka_client import publish_player_event

# ── Rate limiter ───────────────────────────────────────────
# IP-based rate limiting via slowapi. Reads: 60/min, Writes: 10/min.
# Tests disable this via `limiter.enabled = False` in conftest.
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    db = SessionLocal()
    try:
        load_rosters(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="NWSL Roster API",
    description="REST API for Gotham FC and Denver Summit rosters — backed by PostgreSQL",
    version="2.0.0",
    lifespan=lifespan,
)

# Wire the limiter into the app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


# ── GET /teams ─────────────────────────────────────────────
@app.get("/teams", response_model=list[str], tags=["Teams"])
@limiter.limit("60/minute")
def get_teams(request: Request, db: Session = Depends(get_db)):
    return list_teams(db)


# ── GET /teams/{team_name} ─────────────────────────────────
@app.get("/teams/{team_name}", response_model=list[Player], tags=["Teams"])
@limiter.limit("60/minute")
def get_team(request: Request, team_name: str, db: Session = Depends(get_db)):
    players = get_team_players(team_name, db)
    if not players:
        raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found")
    return players


# ── GET /teams/{team_name}/players ─────────────────────────
@app.get("/teams/{team_name}/players", response_model=list[Player], tags=["Teams"])
@limiter.limit("60/minute")
def get_team_players_filtered(
    request: Request,
    team_name: str,
    position: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    min_age: Optional[int] = Query(None),
    max_age: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    players = get_team_players(team_name, db)
    if not players:
        raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found")
    if position:
        players = [p for p in players if p.position.lower() == position.lower()]
    if country:
        players = [p for p in players if p.country.lower() == country.lower()]
    if min_age is not None:
        players = [p for p in players if p.age and p.age >= min_age]
    if max_age is not None:
        players = [p for p in players if p.age and p.age <= max_age]
    return players


# ── GET /players/{name} ────────────────────────────────────
@app.get("/players/{name}", response_model=Player, tags=["Players"])
@limiter.limit("60/minute")
def get_player_endpoint(request: Request, name: str, db: Session = Depends(get_db)):
    player = get_player_by_name(name, db)
    if not player:
        raise HTTPException(status_code=404, detail=f"Player '{name}' not found")
    return player


# ── POST /players ──────────────────────────────────────────
@app.post("/players", response_model=Player, status_code=201, tags=["Players"])
@limiter.limit("10/minute")
def add_player(request: Request, player: Player, db: Session = Depends(get_db)):
    existing = get_player(player.team, player.name, db)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Player '{player.name}' already exists on {player.team}"
        )
    insert_player(player, db)
    publish_player_event("player_added", player.model_dump())
    return player


# ── PUT /players/{name} ────────────────────────────────────
@app.put("/players/{name}", response_model=Player, tags=["Players"])
@limiter.limit("10/minute")
def update_player_endpoint(
    request: Request,
    name: str,
    updates: PlayerUpdate,
    db: Session = Depends(get_db)
):
    row = get_player_row(name, db)
    if not row:
        raise HTTPException(status_code=404, detail=f"Player '{name}' not found")
    update_fields = updates.model_dump(exclude_unset=True)
    updated_row = update_player_row(row, update_fields, db)
    updated_player = Player(
        name=updated_row.name,
        number=updated_row.number,
        age=updated_row.age,
        country=updated_row.country,
        position=updated_row.position,
        team=updated_row.team,
        note=updated_row.note,
    )
    publish_player_event("player_updated", updated_player.model_dump())
    return updated_player


# ── GET /stats/{team_name} ─────────────────────────────────
@app.get("/stats/{team_name}", response_model=SquadStats, tags=["Stats"])
@limiter.limit("60/minute")
def get_squad_stats(request: Request, team_name: str, db: Session = Depends(get_db)):
    players = get_team_players(team_name, db)
    if not players:
        raise HTTPException(status_code=404, detail=f"Team '{team_name}' not found")

    players_with_age = [p for p in players if p.age]
    avg_age = (
        sum(p.age for p in players_with_age) / len(players_with_age)
        if players_with_age else 0
    )
    oldest = max(players_with_age, key=lambda p: p.age) if players_with_age else None
    youngest = min(players_with_age, key=lambda p: p.age) if players_with_age else None
    positions = {}
    for p in players:
        positions[p.position] = positions.get(p.position, 0) + 1

    return SquadStats(
        team=team_name,
        total_players=len(players),
        average_age=round(avg_age, 1),
        countries=sorted(set(p.country for p in players)),
        oldest_player=oldest.name if oldest else "N/A",
        youngest_player=youngest.name if youngest else "N/A",
        positions=positions,
    )
