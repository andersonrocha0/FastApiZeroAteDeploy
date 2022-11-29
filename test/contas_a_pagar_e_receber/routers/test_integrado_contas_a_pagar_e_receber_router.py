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


def test_deve_listar_contas_a_pagar_e_receber():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    client.post("/contas-a-pagar-e-receber", json={'descricao': 'Aluguel', 'valor': 1000.5, 'tipo': 'PAGAR'})
    client.post("/contas-a-pagar-e-receber", json={'descricao': 'Salário', 'valor': 5000, 'tipo': 'RECEBER'})

    response = client.get('/contas-a-pagar-e-receber')
    assert response.status_code == 200
    assert response.json() == [
        {'id': 1, 'descricao': 'Aluguel', 'valor': 1000.5, 'tipo': 'PAGAR', 'fornecedor': None, 'data_baixa': None,
         'valor_baixa': None, 'esta_baixada': False},
        {'id': 2, 'descricao': 'Salário', 'valor': 5000, 'tipo': 'RECEBER', 'fornecedor': None, 'data_baixa': None,
         'valor_baixa': None, 'esta_baixada': False}
    ]


def test_deve_pegar_por_id():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    response = client.post("/contas-a-pagar-e-receber", json={
        "descricao": "Curso de Python",
        "valor": 333,
        "tipo": "PAGAR"
    })

    id_da_conta_a_pagar_e_receber = response.json()['id']

    response_get = client.get(f"/contas-a-pagar-e-receber/{id_da_conta_a_pagar_e_receber}")

    assert response_get.status_code == 200
    assert response_get.json()['valor'] == 333
    assert response_get.json()['tipo'] == "PAGAR"
    assert response_get.json()['descricao'] == "Curso de Python"


def test_deve_retornar_nao_encontrado_para_id_nao_existente():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    response_get = client.get("/contas-a-pagar-e-receber/100")

    assert response_get.status_code == 404


def test_deve_criar_conta_a_pagar_e_receber():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    nova_conta = {
        "descricao": "Curso de Python",
        "valor": 333,
        "tipo": "PAGAR",
        "fornecedor": None,
        'data_baixa': None,
        'valor_baixa': None,
        'esta_baixada': False
    }
    nova_conta_copy = nova_conta.copy()
    nova_conta_copy["id"] = 1

    response = client.post("/contas-a-pagar-e-receber", json=nova_conta)
    assert response.status_code == 201
    assert response.json() == nova_conta_copy


def test_deve_atualizar_conta_a_pagar_e_receber():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    response = client.post("/contas-a-pagar-e-receber", json={
        "descricao": "Curso de Python",
        "valor": 333,
        "tipo": "PAGAR"
    })

    id_da_conta_a_pagar_e_receber = response.json()['id']

    response_put = client.put(f"/contas-a-pagar-e-receber/{id_da_conta_a_pagar_e_receber}", json={
        "descricao": "Curso de Python",
        "valor": 111,
        "tipo": "PAGAR"
    })

    assert response_put.status_code == 200
    assert response_put.json()['valor'] == 111


def test_deve_retornar_nao_encontrado_para_id_nao_existente_na_atualizacao():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    response_put = client.put("/contas-a-pagar-e-receber/100", json={
        "descricao": "Curso de Python",
        "valor": 111,
        "tipo": "PAGAR"
    })

    assert response_put.status_code == 404


def test_deve_remover_conta_a_pagar_e_receber():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    response = client.post("/contas-a-pagar-e-receber", json={
        "descricao": "Curso de Python",
        "valor": 333,
        "tipo": "PAGAR"
    })

    id_da_conta_a_pagar_e_receber = response.json()['id']

    response_put = client.delete(f"/contas-a-pagar-e-receber/{id_da_conta_a_pagar_e_receber}")

    assert response_put.status_code == 204


def test_deve_retornar_nao_encontrado_para_id_nao_existente_na_remocao():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    response_put = client.delete("/contas-a-pagar-e-receber/100")

    assert response_put.status_code == 404


def test_deve_retornar_erro_quando_exceder_a_descricao():
    response = client.post('/contas-a-pagar-e-receber', json={
        "descricao": "0123456789012345678901234567890",
        "valor": 333,
        "tipo": "PAGAR"
    })
    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'] == ["body", "descricao"]


def test_deve_retornar_erro_quando_a_descricao_for_menor_do_que_o_necessario():
    response = client.post('/contas-a-pagar-e-receber', json={
        "descricao": "01",
        "valor": 333,
        "tipo": "PAGAR"
    })
    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'] == ["body", "descricao"]


def test_deve_retornar_erro_quando_o_valor_for_zero_ou_menor():
    response = client.post('/contas-a-pagar-e-receber', json={
        "descricao": "Test",
        "valor": 0,
        "tipo": "PAGAR"
    })
    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'] == ["body", "valor"]

    response = client.post('/contas-a-pagar-e-receber', json={
        "descricao": "Test",
        "valor": -1,
        "tipo": "PAGAR"
    })
    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'] == ["body", "valor"]


def test_deve_retornar_erro_quando_o_tipo_for_invalido():
    response = client.post('/contas-a-pagar-e-receber', json={
        "descricao": "Test",
        "valor": 100,
        "tipo": "INVALIDO"
    })
    assert response.status_code == 422
    assert response.json()['detail'][0]['loc'] == ["body", "tipo"]


def test_deve_criar_conta_a_pagar_e_receber_com_fornecedor_cliente_id():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    novo_fornecedor_cliente = {
        "nome": "Casa da Música"
    }

    client.post("/fornecedor-cliente", json=novo_fornecedor_cliente)

    nova_conta = {
        "descricao": "Curso de Guitarra",
        "valor": 250,
        "tipo": "PAGAR",
        "fornecedor_cliente_id": 1,
        'data_baixa': None,
        'valor_baixa': None,
        'esta_baixada': False
    }

    nova_conta_copy = nova_conta.copy()
    nova_conta_copy["id"] = 1
    nova_conta_copy["fornecedor"] = {
        "id": 1,
        "nome": "Casa da Música"
    }
    del nova_conta_copy['fornecedor_cliente_id']

    response = client.post("/contas-a-pagar-e-receber", json=nova_conta)
    assert response.status_code == 201
    assert response.json() == nova_conta_copy


def test_deve_retornar_erro_ao_inserir_uma_nova_conta_com_fornecedor_invalido():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    nova_conta = {
        "descricao": "Curso de Guitarra",
        "valor": 250,
        "tipo": "PAGAR",
        "fornecedor_cliente_id": 1001
    }

    response = client.post("/contas-a-pagar-e-receber", json=nova_conta)
    assert response.status_code == 422


def test_deve_atualizar_conta_a_pagar_e_receber_com_fornecedor_cliente_id():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    novo_fornecedor_cliente = {
        "nome": "Código e CIA"
    }

    client.post("/fornecedor-cliente", json=novo_fornecedor_cliente)

    response = client.post("/contas-a-pagar-e-receber", json={
        "descricao": "Curso de Python",
        "valor": 333,
        "tipo": "PAGAR"
    })

    id_da_conta_a_pagar_e_receber = response.json()['id']

    response_put = client.put(f"/contas-a-pagar-e-receber/{id_da_conta_a_pagar_e_receber}", json={
        "descricao": "Curso de Python",
        "valor": 111,
        "tipo": "PAGAR",
        "fornecedor_cliente_id": 1
    })

    assert response_put.status_code == 200
    assert response_put.json()["fornecedor"] == {"id": 1, "nome": "Código e CIA"}


def test_deve_retornar_erro_ao_atualizar_uma_nova_conta_com_fornecedor_invalido():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    response = client.post("/contas-a-pagar-e-receber", json={
        "descricao": "Curso de Python",
        "valor": 333,
        "tipo": "PAGAR"
    })

    id_da_conta_a_pagar_e_receber = response.json()['id']

    response_put = client.put(f"/contas-a-pagar-e-receber/{id_da_conta_a_pagar_e_receber}", json={
        "descricao": "Curso de Python",
        "valor": 111,
        "tipo": "PAGAR",
        "fornecedor_cliente_id": 1001
    })

    assert response_put.status_code == 422


def test_deve_baixar_conta():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    client.post("/contas-a-pagar-e-receber", json={
        "descricao": "Curso de Python",
        "valor": 333,
        "tipo": "PAGAR"
    })

    response_acao = client.post(f"/contas-a-pagar-e-receber/1/baixar")

    assert response_acao.status_code == 200
    assert response_acao.json()['esta_baixada'] is True
    assert response_acao.json()['valor'] == 333


def test_deve_baixar_conta_modificada():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    client.post("/contas-a-pagar-e-receber", json={
        "descricao": "Curso de Python",
        "valor": 333,
        "tipo": "PAGAR"
    })

    client.post(f"/contas-a-pagar-e-receber/1/baixar")

    client.put(f"/contas-a-pagar-e-receber/1", json={
        "descricao": "Curso de Python",
        "valor": 444,
        "tipo": "PAGAR"
    })

    response_acao = client.post(f"/contas-a-pagar-e-receber/1/baixar")

    assert response_acao.status_code == 200
    assert response_acao.json()['esta_baixada'] is True
    assert response_acao.json()['valor'] == 444
    assert response_acao.json()['valor_baixa'] == 444
