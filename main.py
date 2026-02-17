from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

import models
from database import SessionLocal, engine

# Criar tabelas no banco
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# ==========================
# CONFIG JWT
# ==========================

SECRET_KEY = "chave_super_secreta"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==========================
# DEPENDÊNCIA DO BANCO
# ==========================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================
# FUNÇÕES AUXILIARES
# ==========================

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ==========================
# ROTAS DE USUÁRIO
# ==========================

@app.post("/register")
def register(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()

    if user:
        raise HTTPException(status_code=400, detail="Usuário já existe")

    hashed_password = hash_password(password)

    new_user = models.User(
        username=username,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Usuário criado com sucesso"}


@app.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()

    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Senha incorreta")

    access_token = create_access_token({"sub": user.username})

    return {"access_token": access_token, "token_type": "bearer"}

# ==========================
# CRUD PESSOAS
# ==========================

@app.post("/pessoas")
def criar_pessoa(nome: str, idade: int, cidade: str, db: Session = Depends(get_db)):
    nova_pessoa = models.Pessoa(
        nome=nome,
        idade=idade,
        cidade=cidade
    )

    db.add(nova_pessoa)
    db.commit()
    db.refresh(nova_pessoa)

    return nova_pessoa


@app.get("/pessoas")
def listar_pessoas(db: Session = Depends(get_db)):
    pessoas = db.query(models.Pessoa).all()
    return pessoas


@app.put("/pessoas/{pessoa_id}")
def atualizar_pessoa(pessoa_id: int, nome: str, idade: int, cidade: str, db: Session = Depends(get_db)):
    pessoa = db.query(models.Pessoa).filter(models.Pessoa.id == pessoa_id).first()

    if not pessoa:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")

    pessoa.nome = nome
    pessoa.idade = idade
    pessoa.cidade = cidade

    db.commit()
    db.refresh(pessoa)

    return pessoa


@app.delete("/pessoas/{pessoa_id}")
def deletar_pessoa(pessoa_id: int, db: Session = Depends(get_db)):
    pessoa = db.query(models.Pessoa).filter(models.Pessoa.id == pessoa_id).first()

    if not pessoa:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")

    db.delete(pessoa)
    db.commit()

    return {"message": "Pessoa deletada com sucesso"}
