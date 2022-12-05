from collections import OrderedDict
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import extract
from sqlalchemy.orm import Session

from contas_a_pagar_e_receber.models.conta_a_pagar_receber_model import ContaPagarReceber
from contas_a_pagar_e_receber.models.fornecedor_cliente_model import FornecedorCliente
from contas_a_pagar_e_receber.routers.fornecedor_cliente_router import FornecedorClienteResponse
from shared.dependencies import get_db
from shared.exceptions import NotFound

router = APIRouter(prefix="/contas-a-pagar-e-receber")

QUANTIDADE_PERMITIDA_POR_MES = 100


class ContaPagarReceberResponse(BaseModel):
    id: int
    descricao: str
    valor: Decimal
    tipo: str  # PAGAR, RECEBER
    data_previsao: date
    data_baixa: date | None = None
    valor_baixa: Decimal | None = None
    esta_baixada: bool | None = None
    fornecedor: FornecedorClienteResponse | None = None

    class Config:
        orm_mode = True


class ContaPagarReceberTipoEnum(str, Enum):
    PAGAR = 'PAGAR'
    RECEBER = 'RECEBER'


class ContaPagarReceberRequest(BaseModel):
    descricao: str = Field(min_length=3, max_length=30)
    valor: Decimal = Field(gt=0)
    tipo: ContaPagarReceberTipoEnum  # PAGAR, RECEBER
    fornecedor_cliente_id: int | None = None
    data_previsao: date


class PrevisaoPorMes(BaseModel):
    mes: int
    valor_total: Decimal


@router.get("", response_model=List[ContaPagarReceberResponse])
def listar_contas(db: Session = Depends(get_db)) -> List[ContaPagarReceberResponse]:
    return db.query(ContaPagarReceber).all()


@router.get("/previsao-gastos-por-mes", response_model=List[PrevisaoPorMes])
def previsa_de_gatos_por_mes(db: Session = Depends(get_db), ano=date.today().year):
    return relatorio_gastos_previstos_por_mes_de_um_ano(db, ano)


@router.get("/{id_da_conta_a_pagar_e_receber}", response_model=ContaPagarReceberResponse)
def obter_conta_por_id(id_da_conta_a_pagar_e_receber: int,
                       db: Session = Depends(get_db)) -> List[ContaPagarReceberResponse]:
    return busca_conta_por_id(id_da_conta_a_pagar_e_receber, db)


@router.post("", response_model=ContaPagarReceberResponse, status_code=201)
def criar_conta(conta_a_pagar_e_receber_request: ContaPagarReceberRequest,
                db: Session = Depends(get_db)) -> ContaPagarReceberResponse:
    valida_fornecedor(conta_a_pagar_e_receber_request.fornecedor_cliente_id, db)

    valida_se_pode_registrar_novas_contas(db=db, conta_a_pagar_e_receber_request=conta_a_pagar_e_receber_request)

    contas_a_pagar_e_receber = ContaPagarReceber(
        **conta_a_pagar_e_receber_request.dict()
    )

    db.add(contas_a_pagar_e_receber)
    db.commit()
    db.refresh(contas_a_pagar_e_receber)

    return contas_a_pagar_e_receber


@router.put("/{id_da_conta_a_pagar_e_receber}", response_model=ContaPagarReceberResponse, status_code=200)
def atualizar_conta(id_da_conta_a_pagar_e_receber: int,
                    conta_a_pagar_e_receber_request: ContaPagarReceberRequest,
                    db: Session = Depends(get_db)) -> ContaPagarReceberResponse:
    valida_fornecedor(conta_a_pagar_e_receber_request.fornecedor_cliente_id, db)

    conta_a_pagar_e_receber = busca_conta_por_id(id_da_conta_a_pagar_e_receber, db)
    conta_a_pagar_e_receber.tipo = conta_a_pagar_e_receber_request.tipo
    conta_a_pagar_e_receber.valor = conta_a_pagar_e_receber_request.valor
    conta_a_pagar_e_receber.descricao = conta_a_pagar_e_receber_request.descricao
    conta_a_pagar_e_receber.fornecedor_cliente_id = conta_a_pagar_e_receber_request.fornecedor_cliente_id

    db.add(conta_a_pagar_e_receber)
    db.commit()
    db.refresh(conta_a_pagar_e_receber)
    return conta_a_pagar_e_receber


@router.post("/{id_da_conta_a_pagar_e_receber}/baixar", response_model=ContaPagarReceberResponse, status_code=200)
def baixar_conta(id_da_conta_a_pagar_e_receber: int,
                 db: Session = Depends(get_db)) -> ContaPagarReceberResponse:
    conta_a_pagar_e_receber = busca_conta_por_id(id_da_conta_a_pagar_e_receber, db)

    if conta_a_pagar_e_receber.esta_baixada and conta_a_pagar_e_receber.valor == conta_a_pagar_e_receber.valor_baixa:
        return conta_a_pagar_e_receber

    conta_a_pagar_e_receber.data_baixa = date.today()
    conta_a_pagar_e_receber.esta_baixada = True
    conta_a_pagar_e_receber.valor_baixa = conta_a_pagar_e_receber.valor

    db.add(conta_a_pagar_e_receber)
    db.commit()
    db.refresh(conta_a_pagar_e_receber)
    return conta_a_pagar_e_receber


@router.delete("/{id_da_conta_a_pagar_e_receber}", status_code=204)
def excluir_conta(id_da_conta_a_pagar_e_receber: int,
                  db: Session = Depends(get_db)) -> None:
    conta_a_pagar_e_receber = busca_conta_por_id(id_da_conta_a_pagar_e_receber, db)

    db.delete(conta_a_pagar_e_receber)
    db.commit()


def busca_conta_por_id(id_da_conta_a_pagar_e_receber: int, db: Session) -> ContaPagarReceber:
    conta_a_pagar_e_receber = db.query(ContaPagarReceber).get(id_da_conta_a_pagar_e_receber)

    if conta_a_pagar_e_receber is None:
        raise NotFound("Conta a Pagar e Receber")

    return conta_a_pagar_e_receber


def valida_fornecedor(fornecedor_cliente_id, db):
    if fornecedor_cliente_id is not None:
        conta_a_pagar_e_receber = db.query(FornecedorCliente).get(fornecedor_cliente_id)
        if conta_a_pagar_e_receber is None:
            raise HTTPException(status_code=422, detail="Esse fornecedor não existe no banco de dados")


def valida_se_pode_registrar_novas_contas(
        conta_a_pagar_e_receber_request: ContaPagarReceberRequest,
        db: Session) -> None:
    if recupera_numero_registros(db,
                                 conta_a_pagar_e_receber_request.data_previsao.year,
                                 conta_a_pagar_e_receber_request.data_previsao.month) >= QUANTIDADE_PERMITIDA_POR_MES:
        raise HTTPException(status_code=422, detail="Você não pode mais lançar contas para esse mês")


def recupera_numero_registros(db, ano, mes) -> int:
    quantidade_de_registros = db.query(ContaPagarReceber).filter(
        extract('year', ContaPagarReceber.data_previsao) == ano
    ).filter(
        extract('month', ContaPagarReceber.data_previsao) == mes
    ).count()

    return quantidade_de_registros


def relatorio_gastos_previstos_por_mes_de_um_ano(db, ano) -> List[PrevisaoPorMes]:
    contas = db.query(ContaPagarReceber).filter(
        extract('year', ContaPagarReceber.data_previsao) == ano
    ).filter(
        ContaPagarReceber.tipo == ContaPagarReceberTipoEnum.PAGAR
    ).order_by(ContaPagarReceber.data_previsao).all()

    valor_por_mes = OrderedDict()

    for conta in contas:

        mes = conta.data_previsao.month

        if valor_por_mes.get(mes) is None:
            valor_por_mes[mes] = 0

        valor_por_mes[mes] += conta.valor

    return [PrevisaoPorMes(mes=k, valor_total=v) for k, v in valor_por_mes.items()]

    # for k, g in groupby(contas, lambda x: x.data_previsao.month):
    #     print({k: sum([v.valor for v in g])})
