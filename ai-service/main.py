from fastapi import FastAPI
from api.routes import router

app = FastAPI(
    title="SkillGap AI Analytics Service",
    version="0.1.0",
)

app.include_router(router)

@app.get("/")
def root():
    return {
        "service": "skillgap-ai",
        "status": "running",
    }
