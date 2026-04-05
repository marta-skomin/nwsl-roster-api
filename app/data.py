from sqlalchemy.orm import Session
from app.database import PlayerDB
from app.models import Player

def player_from_db(row: PlayerDB) -> Player:
    return Player(
        name=row.name,
        number=row.number,
        age=row.age,
        country=row.country,
        position=row.position,
        team=row.team,
        note=row.note,
    )

def load_rosters(db: Session):
    """Seed the database if empty."""
    if db.query(PlayerDB).count() > 0:
        print("Database already seeded — skipping")
        return

    from app.seed_data import TEAMS
    count = 0
    for team_name, roster in TEAMS.items():
        for p in roster:
            row = PlayerDB(team=team_name, **p)
            db.add(row)
            count += 1
    db.commit()
    print(f"Seeded {count} players into PostgreSQL")

def list_teams(db: Session) -> list[str]:
    rows = db.query(PlayerDB.team).distinct().all()
    return [r.team for r in rows]

def get_team_players(team_name: str, db: Session) -> list[Player]:
    rows = db.query(PlayerDB).filter(PlayerDB.team == team_name).all()
    return [player_from_db(r) for r in rows]

def get_player(team_name: str, player_name: str, db: Session) -> Player | None:
    row = db.query(PlayerDB).filter(
        PlayerDB.team == team_name,
        PlayerDB.name.ilike(player_name)
    ).first()
    return player_from_db(row) if row else None

def get_player_by_name(player_name: str, db: Session) -> Player | None:
    row = db.query(PlayerDB).filter(
        PlayerDB.name.ilike(player_name)
    ).first()
    return player_from_db(row) if row else None

def get_player_row(player_name: str, db: Session) -> PlayerDB | None:
    return db.query(PlayerDB).filter(
        PlayerDB.name.ilike(player_name)
    ).first()

def insert_player(player: Player, db: Session) -> PlayerDB:
    row = PlayerDB(
        name=player.name,
        number=player.number,
        age=player.age,
        country=player.country,
        position=player.position,
        team=player.team,
        note=player.note,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

def update_player_row(row: PlayerDB, updates: dict, db: Session) -> PlayerDB:
    for key, value in updates.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row

