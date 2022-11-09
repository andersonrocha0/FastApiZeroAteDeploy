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


def test_deve_listar_fornecedor_cliente():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    client.post("/fornecedor-cliente", json={'nome': 'CPFL'})
    client.post("/fornecedor-cliente", json={'nome': 'Sanasa'})

    response = client.get('/fornecedor-cliente')
    assert response.status_code == 200
    assert response.json() == [
        {'id': 1, 'nome': 'CPFL'},
        {'id': 2, 'nome': 'Sanasa'}
    ]


def test_deve_pegar_por_id():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    response = client.post("/fornecedor-cliente", json={'nome': 'CPFL'})

    id_do_fornecedor_cliente = response.json()['id']

    response_get = client.get(f"/fornecedor-cliente/{id_do_fornecedor_cliente}")

    assert response_get.status_code == 200
    assert response_get.json()['nome'] == "CPFL"


def test_deve_retornar_nao_encontrado_para_id_nao_existente():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    response_get = client.get("/fornecedor-cliente/100")

    assert response_get.status_code == 404


def test_deve_criar_fornecedor_cliente():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    novo_fornecedor_cliente = {
        "nome": "Extra Super Mercados"

    }

    novo_fornecedor_cliente_copy = novo_fornecedor_cliente.copy()
    novo_fornecedor_cliente_copy["id"] = 1

    response = client.post("/fornecedor-cliente", json=novo_fornecedor_cliente)
    assert response.status_code == 201
    assert response.json() == novo_fornecedor_cliente_copy


def test_deve_atualizar_fornecedor_cliente():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    response = client.post("/fornecedor-cliente", json={
        "nome": "Extra Super Mercados"
    })

    id_do_fornecedor_cliente = response.json()['id']

    response_put = client.put(f"/fornecedor-cliente/{id_do_fornecedor_cliente}", json={
        "nome": "Giga Extra"
    })

    assert response_put.status_code == 200
    assert response_put.json()['nome'] == "Giga Extra"


def test_deve_retornar_nao_encontrado_para_id_nao_existente_na_atualizacao():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    response_put = client.put("/fornecedor-cliente/100", json={
        "nome": "Giga Extra"
    })

    assert response_put.status_code == 404


def test_deve_remover_fornecedor_cliente():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    response = client.post("/fornecedor-cliente", json={
        "nome": "Adde Sistemas"
    })

    id_do_fornecedor_cliente = response.json()['id']

    response_put = client.delete(f"/fornecedor-cliente/{id_do_fornecedor_cliente}")

    assert response_put.status_code == 204

    response_get_all = client.get("/fornecedor-cliente")

    assert len(response_get_all.json()) == 0


def test_deve_retornar_nao_encontrado_para_id_nao_existente_na_remocao():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    response_put = client.delete("/fornecedor-cliente/100")

    assert response_put.status_code == 404


def test_deve_retornar_erro_quando_o_nome_nao_estiver_dentro_dos_limites():
    response = client.post('/fornecedor-cliente', json={
        "nome": "AS"
    })
    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'] == ["body", "nome"]

    response2 = client.post('/fornecedor-cliente', json={
        "nome": "ASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGASDFGA"
    })
    assert response2.status_code == 422
    assert response2.json()['detail'][0]['loc'] == ["body", "nome"]
