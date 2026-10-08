from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlmodel import Field, SQLModel, create_engine, Session, select

class Recipe(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str

sqlite_file_name = 'database.db'
sqlite_url = f'sqlite:///{sqlite_file_name}'
engine = create_engine(sqlite_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

@app.get('/')
def read_root():
    return { 'message': 'Baza danych dziala' }

@app.post('/recipes/')
def create_recipe(title: str, description: str):
    with Session(engine) as session:
        recipe = Recipe(title=title, description=description)
        session.add(recipe)
        session.commit()
        session.refresh(recipe)
        return recipe

@app.get('/recipes/')
def get_recipes():
    with Session(engine) as session:
        recipes = session.exec(select(Recipe)).all()
        return recipes