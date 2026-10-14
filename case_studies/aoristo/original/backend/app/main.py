"""Research-only bootstrap; original sale, purchase and invitation routers."""
from fastapi import FastAPI
from app.infrastructure.api.routes.sale_routes import router as sales
from app.infrastructure.api.routes.purchase_routes import router as purchases
from app.infrastructure.api.routes.invitation_routes import router as invitations
app=FastAPI(title="AoristoTech extracted research case")
for router in (sales,purchases,invitations):
    app.include_router(router,prefix="/api")
