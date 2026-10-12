from fastapi import FastAPI

from core.database import lifespan
from routes.auth import router as auth_router
from routes.users import router as users_router


app = FastAPI(
    title='Recipe Recommender API',
    description='API with a ML model for recipe recommendation.',
    version='1.0.0',
    lifespan=lifespan
)

app.include_router(auth_router)
app.include_router(users_router)


@app.get('/')
def read_root():
    return {
        'message': 'FastAPI backend is running successfully!'
    }