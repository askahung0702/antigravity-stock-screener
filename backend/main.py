from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.valuation_router import router as valuation_router
from routers.screener_router import router as screener_router
from routers.news_router import router as news_router
from routers.system_router import router as system_router

app = FastAPI(title="Taiwan Stock Analysis API")

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(valuation_router)
app.include_router(screener_router)
app.include_router(news_router)
app.include_router(system_router)

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Backend is running!"}
