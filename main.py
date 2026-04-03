from fastapi import FastAPI

app = FastAPI(title="NWSL Roster API")

@app.get("/")
def root():
    return {"message": "National Women's Soccer League API"}

@app.get('/teams')
def teams(): 
    return {'clubs': ["NJ/NY Gotham FC", "Denver Summit FC"]} 

