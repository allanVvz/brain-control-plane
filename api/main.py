from fastapi import FastAPI
from middleware.auth import auth_middleware
from routes import (access, assets, audiences, auth, generation, graph,
                    graph_bundles, graph_documents, graph_projections,
                    health, integrations, kb, kb_intake, knowledge, logs,
                    marketing, menu, messaging_campaigns, personas, pipeline, portal,
                    public_site_formats)

app = FastAPI(title="Brain Control Plane", version="1.0.0")
app.middleware("http")(auth_middleware)
for router in (health.router, auth.router, access.router, portal.router,
               personas.router, integrations.router, kb.router,
               knowledge.router, pipeline.router, kb_intake.router,
               generation.router, graph.router, graph_documents.router,
               graph_bundles.router, graph_projections.router,
               marketing.router, messaging_campaigns.router, audiences.router, assets.router,
               menu.router, public_site_formats.router, logs.router):
    app.include_router(router)
