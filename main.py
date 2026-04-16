import logging

from fastapi import FastAPI

from app.routes.agent_router import router as agent_router
from app.routes.cep_route import router as cep_router
from app.routes.weather_route import router as weather_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = FastAPI(
    title="Proj_Autocapacita_p2",
    version="0.1.0",
    description="este é um projeto de teste para autocapacitação "
                "em desenvolvimento back end com foco em apis e agentes de IA",
)

app.include_router(cep_router, prefix="/api")
app.include_router(weather_router, prefix="/api")
app.include_router(agent_router, prefix="/api/agent")


@app.get("/")
def read_root():
    """Endpoint inicial para teste da API."""
    return {"message": "API funcionando!"}
