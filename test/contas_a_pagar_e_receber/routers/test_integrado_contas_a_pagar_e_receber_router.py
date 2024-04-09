import datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from contas_a_pagar_e_receber.routers.contas_a_pagar_e_receber_router import QUANTIDADE_PERMITIDA_POR_MES
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

    client.post("/contas-a-pagar-e-receber",
                json={'descricao': 'Aluguel', 'valor': 1000.5, 'tipo': 'PAGAR', 'data_previsao': '2022-11-29'})
    client.post("/contas-a-pagar-e-receber",
                json={'descricao': 'Salário', 'valor': 5000, 'tipo': 'RECEBER', 'data_previsao': '2022-11-29'})

    response = client.get('/contas-a-pagar-e-receber')
    assert response.status_code == 200
    assert response.json() == [
        {'id': 1, 'descricao': 'Aluguel', 'valor': "1000.50", 'tipo': 'PAGAR', 'fornecedor': None, 'data_baixa': None,
         'valor_baixa': None, 'esta_baixada': False, 'data_previsao': '2022-11-29'},
        {'id': 2, 'descricao': 'Salário', 'valor': "5000.00", 'tipo': 'RECEBER', 'fornecedor': None, 'data_baixa': None,
         'valor_baixa': None, 'esta_baixada': False, 'data_previsao': '2022-11-29'}
    ]


def test_deve_pegar_por_id():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    response = client.post("/contas-a-pagar-e-receber", json={
        "descricao": "Curso de Python",
        "valor": 333,
        "tipo": "PAGAR",
        'data_previsao': '2022-11-29'
    })

    id_da_conta_a_pagar_e_receber = response.json()['id']

    response_get = client.get(f"/contas-a-pagar-e-receber/{id_da_conta_a_pagar_e_receber}")

    assert response_get.status_code == 200
    assert response_get.json()['valor'] == "333.00"
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
        'data_previsao': '2022-11-29'
    }
    nova_conta_copy = nova_conta.copy()
    nova_conta_copy["id"] = 1
    nova_conta_copy["fornecedor"] = None
    nova_conta_copy['data_baixa'] = None
    nova_conta_copy['valor_baixa'] = None
    nova_conta_copy['esta_baixada'] = False
    nova_conta_copy['valor'] = "333.00"

    response = client.post("/contas-a-pagar-e-receber", json=nova_conta)
    assert response.status_code == 201
    assert response.json() == nova_conta_copy


def test_deve_atualizar_conta_a_pagar_e_receber():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    response = client.post("/contas-a-pagar-e-receber", json={
        "descricao": "Curso de Python",
        "valor": 333,
        "tipo": "PAGAR",
        "data_previsao": "2022-11-29"
    })

    id_da_conta_a_pagar_e_receber = response.json()['id']

    response_put = client.put(f"/contas-a-pagar-e-receber/{id_da_conta_a_pagar_e_receber}", json={
        "descricao": "Curso de Python",
        "valor": 111,
        "tipo": "PAGAR",
        "data_previsao": "2022-11-29"
    })

    assert response_put.status_code == 200
    assert response_put.json()['valor'] == "111.00"


def test_deve_retornar_nao_encontrado_para_id_nao_existente_na_atualizacao():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    response_put = client.put("/contas-a-pagar-e-receber/100", json={
        "descricao": "Curso de Python",
        "valor": 111,
        "tipo": "PAGAR",
        "data_previsao": "2022-11-29"
    })

    assert response_put.status_code == 404


def test_deve_remover_conta_a_pagar_e_receber():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    response = client.post("/contas-a-pagar-e-receber", json={
        "descricao": "Curso de Python",
        "valor": 333,
        "tipo": "PAGAR",
        "data_previsao": "2022-11-29"
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
        "data_previsao": "2022-11-29"
    }

    nova_conta_copy = nova_conta.copy()
    nova_conta_copy["id"] = 1
    nova_conta_copy["fornecedor"] = {
        "id": 1,
        "nome": "Casa da Música"
    }
    del nova_conta_copy['fornecedor_cliente_id']
    nova_conta_copy['data_baixa'] = None
    nova_conta_copy['valor_baixa'] = None
    nova_conta_copy['esta_baixada'] = False
    nova_conta_copy['valor'] = "250.00"

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
        "fornecedor_cliente_id": 1001,
        "data_previsao": "2022-11-29"
    }

    response = client.post("/contas-a-pagar-e-receber", json=nova_conta)
    assert response.status_code == 422
    assert response.json()['detail'] == 'Esse fornecedor não existe no banco de dados'


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
        "tipo": "PAGAR",
        "data_previsao": "2022-11-29"
    })

    id_da_conta_a_pagar_e_receber = response.json()['id']

    response_put = client.put(f"/contas-a-pagar-e-receber/{id_da_conta_a_pagar_e_receber}", json={
        "descricao": "Curso de Python",
        "valor": 111,
        "tipo": "PAGAR",
        "fornecedor_cliente_id": 1,
        "data_previsao": "2022-11-29"
    })

    assert response_put.status_code == 200
    assert response_put.json()["fornecedor"] == {"id": 1, "nome": "Código e CIA"}


def test_deve_retornar_erro_ao_atualizar_uma_nova_conta_com_fornecedor_invalido():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    response = client.post("/contas-a-pagar-e-receber", json={
        "descricao": "Curso de Python",
        "valor": 333,
        "tipo": "PAGAR",
        "data_previsao": "2022-11-29"
    })

    id_da_conta_a_pagar_e_receber = response.json()['id']

    response_put = client.put(f"/contas-a-pagar-e-receber/{id_da_conta_a_pagar_e_receber}", json={
        "descricao": "Curso de Python",
        "valor": 111,
        "tipo": "PAGAR",
        "fornecedor_cliente_id": 1001,
        "data_previsao": "2022-11-29"
    })

    assert response_put.status_code == 422
    assert response_put.json()['detail'] == 'Esse fornecedor não existe no banco de dados'


def test_deve_baixar_conta():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    client.post("/contas-a-pagar-e-receber", json={
        "descricao": "Curso de Python",
        "valor": 333,
        "tipo": "PAGAR",
        "data_previsao": "2022-11-29"
    })

    response_acao = client.post(f"/contas-a-pagar-e-receber/1/baixar")

    assert response_acao.status_code == 200
    assert response_acao.json()['esta_baixada'] is True
    assert response_acao.json()['valor'] == "333.00"


def test_deve_baixar_conta_modificada():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    client.post("/contas-a-pagar-e-receber", json={
        "descricao": "Curso de Python",
        "valor": 333,
        "tipo": "PAGAR",
        "data_previsao": "2022-11-29"
    })

    client.post(f"/contas-a-pagar-e-receber/1/baixar")

    client.put(f"/contas-a-pagar-e-receber/1", json={
        "descricao": "Curso de Python",
        "valor": 444,
        "tipo": "PAGAR",
        "data_previsao": "2022-11-29"
    })

    response_acao = client.post(f"/contas-a-pagar-e-receber/1/baixar")

    assert response_acao.status_code == 200
    assert response_acao.json()['esta_baixada'] is True
    assert response_acao.json()['valor'] == "444.00"
    assert response_acao.json()['valor_baixa'] == "444.00"


def test_limite_de_registros_mensais():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    respostas = []
    for i in range(0, QUANTIDADE_PERMITIDA_POR_MES + 1):
        resposta = client.post("/contas-a-pagar-e-receber", json={
            'descricao': 'Curso Python',
            'valor': 1000.5,
            'tipo': 'PAGAR',
            'data_previsao': '2022-11-29'
        })

        respostas.append(resposta)

    ultima_resposta = respostas.pop()
    assert ultima_resposta.status_code == 422
    assert ultima_resposta.json()['detail'] == 'Você não pode mais lançar contas para esse mês'
    assert all([r.status_code == 201 for r in respostas]) is True


def test_relatorio_gastos_previstos_por_mes_de_um_ano():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    valor = 10
    mes = 1
    for i in range(1, 49):

        mes_com_zero = str(mes).zfill(2)
        ano = datetime.date.today().year

        data = f"{ano}-{mes_com_zero}-01"

        client.post("/contas-a-pagar-e-receber", json={
            'descricao': 'Teste',
            'valor': valor,
            'tipo': 'PAGAR',
            'data_previsao': data
        })

        valor += 10

        if i % 4 == 0:
            mes += 1

    resposta = client.get("/contas-a-pagar-e-receber/previsao-gastos-por-mes")

    assert resposta.status_code == 200
    resultados = resposta.json()
    assert len(resultados) == 12

    valor = 0
    idx = 0
    valor_total = 0
    for i in range(1, 49):
        valor += 10

        valor_total += valor

        if i % 4 == 0:
            assert resultados[idx]['valor_total'] == f"{valor_total}.00"
            valor_total = 0
            idx += 1


def test_relatorio_gastos_previstos_por_mes_sem_registros_no_banco():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    resposta = client.get("/contas-a-pagar-e-receber/previsao-gastos-por-mes")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 0


def test_relatorio_gastos_previstos_por_mes_de_um_ano_sem_registros():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    resposta = client.get("/contas-a-pagar-e-receber/previsao-gastos-por-mes?ano=1990")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 0
