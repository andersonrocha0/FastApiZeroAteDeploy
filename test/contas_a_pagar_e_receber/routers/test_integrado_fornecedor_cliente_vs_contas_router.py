from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from shared.database import Base
from shared.dependencies import get_db

client = TestClient(app)

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def test_deve_listar_contas_de_um_fornecedor_cliente():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    client.post("/fornecedor-cliente", json={'nome': 'Casa da Música'})
    client.post("/fornecedor-cliente", json={'nome': 'Adde Treinamentos'})

    client.post("/contas-a-pagar-e-receber", json={
        'descricao': 'Curso Python',
        'valor': 1000.5,
        'tipo': 'PAGAR',
        'fornecedor_cliente_id': 2,
        "data_previsao": "2022-11-29"
    })
    client.post("/contas-a-pagar-e-receber", json={
        'descricao': 'Curso de Guitarra',
        'valor': 5000,
        'tipo': 'PAGAR',
        'fornecedor_cliente_id': 1,
        "data_previsao": "2022-11-29"
    })
    client.post("/contas-a-pagar-e-receber", json={
        'descricao': 'Curso de Baixo',
        'valor': 6000,
        'tipo': 'PAGAR',
        'fornecedor_cliente_id': 1,
        "data_previsao": "2022-11-29"

    })

    response_get_fornecedor_1 = client.get(f"/fornecedor-cliente/1/contas-a-pagar-e-receber")

    assert response_get_fornecedor_1.status_code == 200
    assert len(response_get_fornecedor_1.json()) == 2

    response_get_fornecedor_2 = client.get(f"/fornecedor-cliente/2/contas-a-pagar-e-receber")

    assert response_get_fornecedor_2.status_code == 200
    assert len(response_get_fornecedor_2.json()) == 1


def test_deve_retornar_uma_lista_vazia_de_contas_de_um_fornecedor_cliente():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    client.post("/fornecedor-cliente", json={'nome': 'Casa da Música'})

    response_get_fornecedor = client.get(f"/fornecedor-cliente/1/contas-a-pagar-e-receber")

    assert response_get_fornecedor.status_code == 200
    assert len(response_get_fornecedor.json()) == 0
