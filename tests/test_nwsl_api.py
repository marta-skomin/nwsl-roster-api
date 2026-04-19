"""
NWSL Roster API — Test Suite
Run from project root: pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app, limiter
from app.database import Base, get_db

# ── Test database setup ───────────────────────────────────
# Use an in-memory SQLite database for tests — fast, isolated, no cleanup needed
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}  # required for SQLite + threading
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def override_get_db():
    """Replace the real DB session with a test session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def setup_test_db():
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    # seed with minimal test data
    db = TestingSessionLocal()
    from app.database import PlayerDB
    db.add_all([
        PlayerDB(name="Rose Lavelle", number=16, age=29, country="USA",
                 position="Midfielder", team="gotham-fc"),
        PlayerDB(name="Ann-Katrin Berger", number=1, age=32, country="Germany",
                 position="Goalkeeper", team="gotham-fc"),
        PlayerDB(name="Midge Purce", number=9, age=29, country="USA",
                 position="Forward", team="gotham-fc"),
        PlayerDB(name="Lindsey Heaps", number=10, age=31, country="USA",
                 position="Midfielder", team="denver-summit",
                 note="USWNT Captain"),
        PlayerDB(name="Melissa Kössler", number=25, age=26, country="Germany",
                 position="Forward", team="denver-summit",
                 note="Top scorer 3 goals"),
    ])
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    """Test client with DB dependency overridden."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# ── GET /teams ────────────────────────────────────────────
class TestGetTeams:
    def test_returns_list(self, client):
        response = client.get("/teams")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_contains_both_teams(self, client):
        response = client.get("/teams")
        teams = response.json()
        assert "gotham-fc" in teams
        assert "denver-summit" in teams

# ── GET /teams/{team_name} ────────────────────────────────
class TestGetTeam:
    def test_gotham_returns_players(self, client):
        response = client.get("/teams/gotham-fc")
        assert response.status_code == 200
        players = response.json()
        assert len(players) == 3
        names = [p["name"] for p in players]
        assert "Rose Lavelle" in names

    def test_unknown_team_returns_404(self, client):
        response = client.get("/teams/nonexistent-fc")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_response_has_required_fields(self, client):
        response = client.get("/teams/gotham-fc")
        player = response.json()[0]
        for field in ["name", "number", "age", "country", "position", "team"]:
            assert field in player

# ── GET /teams/{team_name}/players with filters ───────────
class TestGetTeamPlayersFiltered:
    def test_filter_by_position(self, client):
        response = client.get("/teams/gotham-fc/players?position=Midfielder")
        assert response.status_code == 200
        players = response.json()
        assert len(players) == 1
        assert players[0]["name"] == "Rose Lavelle"

    def test_filter_by_country(self, client):
        response = client.get("/teams/gotham-fc/players?country=Germany")
        assert response.status_code == 200
        players = response.json()
        assert len(players) == 1
        assert players[0]["name"] == "Ann-Katrin Berger"

    def test_filter_by_min_age(self, client):
        response = client.get("/teams/gotham-fc/players?min_age=30")
        assert response.status_code == 200
        players = response.json()
        assert all(p["age"] >= 30 for p in players)

    def test_filter_by_max_age(self, client):
        response = client.get("/teams/gotham-fc/players?max_age=29")
        assert response.status_code == 200
        players = response.json()
        assert all(p["age"] <= 29 for p in players)

    def test_combined_filters(self, client):
        response = client.get("/teams/gotham-fc/players?country=USA&position=Forward")
        assert response.status_code == 200
        players = response.json()
        assert all(p["country"] == "USA" and p["position"] == "Forward" for p in players)

    def test_no_results_returns_empty_list(self, client):
        response = client.get("/teams/gotham-fc/players?country=Brazil")
        assert response.status_code == 200
        assert response.json() == []

# ── GET /players/{name} ───────────────────────────────────
class TestGetPlayer:
    def test_known_player_returns_200(self, client):
        response = client.get("/players/Rose Lavelle")
        assert response.status_code == 200
        assert response.json()["name"] == "Rose Lavelle"
        assert response.json()["team"] == "gotham-fc"

    def test_unknown_player_returns_404(self, client):
        response = client.get("/players/Alex Morgan")
        assert response.status_code == 404

    def test_player_with_note(self, client):
        response = client.get("/players/Lindsey Heaps")
        assert response.status_code == 200
        assert response.json()["note"] == "USWNT Captain"

# ── POST /players ─────────────────────────────────────────
class TestAddPlayer:
    NEW_PLAYER = {
        "name": "Alex Morgan",
        "number": 13,
        "age": 34,
        "country": "USA",
        "position": "Forward",
        "team": "gotham-fc",
    }

    def test_add_new_player_returns_201(self, client):
        response = client.post("/players", json=self.NEW_PLAYER)
        assert response.status_code == 201
        assert response.json()["name"] == "Alex Morgan"

    def test_added_player_is_retrievable(self, client):
        client.post("/players", json=self.NEW_PLAYER)
        response = client.get("/players/Alex Morgan")
        assert response.status_code == 200
        assert response.json()["number"] == 13

    def test_duplicate_player_returns_409(self, client):
        client.post("/players", json=self.NEW_PLAYER)
        response = client.post("/players", json=self.NEW_PLAYER)
        assert response.status_code == 409

    def test_missing_required_field_returns_422(self, client):
        bad_player = {"name": "No Country Player", "position": "Forward", "team": "gotham-fc"}
        response = client.post("/players", json=bad_player)
        assert response.status_code == 422

# ── PUT /players/{name} ───────────────────────────────────
class TestUpdatePlayer:
    def test_update_age(self, client):
        response = client.put("/players/Rose Lavelle", json={"age": 30})
        assert response.status_code == 200
        assert response.json()["age"] == 30

    def test_update_note(self, client):
        response = client.put("/players/Rose Lavelle", json={"note": "Team captain"})
        assert response.status_code == 200
        assert response.json()["note"] == "Team captain"

    def test_update_unknown_player_returns_404(self, client):
        response = client.put("/players/Unknown Player", json={"age": 25})
        assert response.status_code == 404

    def test_partial_update_preserves_other_fields(self, client):
        response = client.put("/players/Rose Lavelle", json={"age": 30})
        data = response.json()
        assert data["name"] == "Rose Lavelle"
        assert data["country"] == "USA"
        assert data["position"] == "Midfielder"

# ── GET /stats/{team_name} ────────────────────────────────
class TestSquadStats:
    def test_stats_returns_200(self, client):
        response = client.get("/stats/gotham-fc")
        assert response.status_code == 200

    def test_stats_total_players(self, client):
        response = client.get("/stats/gotham-fc")
        assert response.json()["total_players"] == 3

    def test_stats_has_required_fields(self, client):
        response = client.get("/stats/gotham-fc")
        data = response.json()
        for field in ["team", "total_players", "average_age", "countries",
                      "oldest_player", "youngest_player", "positions"]:
            assert field in data

    def test_stats_countries_sorted(self, client):
        response = client.get("/stats/gotham-fc")
        countries = response.json()["countries"]
        assert countries == sorted(countries)

    def test_stats_unknown_team_returns_404(self, client):
        response = client.get("/stats/fake-fc")
        assert response.status_code == 404

    def test_stats_oldest_player(self, client):
        response = client.get("/stats/gotham-fc")
        # Ann-Katrin Berger is 32 — oldest in test data
        assert response.json()["oldest_player"] == "Ann-Katrin Berger"

    def test_stats_youngest_player(self, client):
        response = client.get("/stats/gotham-fc")
        # Rose Lavelle is 29, Midge Purce is 29 — youngest tied
        assert response.json()["youngest_player"] in ["Rose Lavelle", "Midge Purce"]



class TestRateLimiter:
    def test_rate_limit_enforced(self, client):
        """Verify rate limiting returns 429 when limit exceeded."""
        limiter.enabled = True
        try:
            # POST /players limit is 10/minute — fire 11 requests
            responses = []
            for i in range(11):
                r = client.post("/players", json={
                    "name": f"Test Player {i}",
                    "number": 99 + i,
                    "age": 25,
                    "country": "USA",
                    "position": "MF",
                    "team": "Gotham FC",
                })
                responses.append(r.status_code)
            assert 429 in responses, "Expected at least one 429 after exceeding limit"
        finally:
            limiter.enabled = False    
