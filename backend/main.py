from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.database import lifespan
from routes.auth import router as auth_router
from routes.recipes import router as recipes_router
from routes.users import router as users_router


app = FastAPI(
    title='Recipe Recommender API',
    description='API with a ML model for recipe recommendation.',
    version='1.0.0',
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

app.include_router(auth_router)
app.include_router(recipes_router)
app.include_router(users_router)


@app.get('/')
def read_root():
    return {
        'message': 'FastAPI backend is running successfully!'
    }