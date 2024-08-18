from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import jwt
import secrets

# Конфигурация базы данных
DATABASE_URL = "postgresql://test_user:test_pass@db:5432/humans_db"
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

# Настройка SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Определение модели Human
class Human(Base):
    __tablename__ = "humans"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    sex = Column(String, nullable=False)

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Модель для Pydantic (для сериализации/десериализации)
class HumanBase(BaseModel):
    name: str
    age: int
    sex: str

class HumanCreate(HumanBase):
    pass

class HumanOut(HumanBase):
    id: int

    class Config:
        orm_mode = True

# Создание FastAPI приложения
app = FastAPI()

# OAuth2 схема для JWT токенов
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Временное хранилище API ключа
api_key = None

# Функция для создания токена
def create_jwt_token(username: str):
    to_encode = {
        "sub": username,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Зависимость для получения текущей сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Зависимость для проверки токена
def token_required(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get("/", response_model=str)
def hello(token: str = Depends(token_required)):
    return "Привет!"

@app.post("/login", response_model=dict)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username == "admin" and form_data.password == "password":
        token = create_jwt_token(form_data.username)
        return {"token": token}
    raise HTTPException(status_code=400, detail="Invalid credentials")

@app.get("/humans", response_model=List[HumanOut])
def get_humans(db: Session = Depends(get_db), token: str = Depends(token_required)):
    humans = db.query(Human).all()
    return humans

@app.get("/humans/{id}", response_model=HumanOut)
def get_human(id: int, db: Session = Depends(get_db), token: str = Depends(token_required)):
    human = db.query(Human).filter(Human.id == id).first()
    if human is None:
        raise HTTPException(status_code=404, detail="Human not found")
    return human

@app.post("/humans", response_model=HumanOut, status_code=201)
def create_human(human: HumanCreate, db: Session = Depends(get_db), token: str = Depends(token_required)):
    db_human = Human(**human.dict())
    db.add(db_human)
    db.commit()
    db.refresh(db_human)
    return db_human

@app.put("/humans/{id}", response_model=HumanOut)
def update_human(id: int, human: HumanCreate, db: Session = Depends(get_db), token: str = Depends(token_required)):
    db_human = db.query(Human).filter(Human.id == id).first()
    if db_human is None:
        raise HTTPException(status_code=404, detail="Human not found")
    db_human.name = human.name
    db_human.age = human.age
    db_human.sex = human.sex
    db.commit()
    db.refresh(db_human)
    return db_human

@app.delete("/humans/{id}", status_code=204)
def delete_human(id: int, db: Session = Depends(get_db), token: str = Depends(token_required)):
    db_human = db.query(Human).filter(Human.id == id).first()
    if db_human is None:
        raise HTTPException(status_code=404, detail="Human not found")
    db.delete(db_human)
    db.commit()
    return {"message": f"id {id} deleted"}
