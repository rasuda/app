import fcntl
import html
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st


st.set_page_config(
    page_title="Controle de Veículos",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ARQUIVO_JSON = Path(__file__).with_name("veiculos.json")
ARQUIVO_LOCK = Path(__file__).with_name("veiculos.lock")
FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")

# Usado somente na primeira execução, quando veiculos.json ainda não existe.
FROTA_INICIAL = [
    {"id": f"VEI-{numero:03d}", "nome": f"Veículo {numero:02d}"}
    for numero in range(1, 11)
]


def agora() -> str:
    return datetime.now(FUSO_HORARIO).strftime("%d/%m/%Y %H:%M:%S")


def dados_iniciais() -> dict:
    return {
        "veiculos": [
            {**veiculo, "responsavel": None} for veiculo in FROTA_INICIAL
        ],
        "historico": [
            {
                "data_hora": agora(),
                "movimento": "Frota inicial criada",
                "veiculo": "10 veículos",
                "id": "—",
                "responsavel": "—",
            }
        ],
    }


def ler_sem_lock() -> dict:
    if not ARQUIVO_JSON.exists():
        return dados_iniciais()
    with ARQUIVO_JSON.open("r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)
    dados.setdefault("veiculos", [])
    dados.setdefault("historico", [])
    return dados


def salvar_sem_lock(dados: dict) -> None:
    descritor, caminho_temporario = tempfile.mkstemp(
        prefix="veiculos_", suffix=".json", dir=ARQUIVO_JSON.parent
    )
    try:
        with os.fdopen(descritor, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(caminho_temporario, ARQUIVO_JSON)
    finally:
        if os.path.exists(caminho_temporario):
            os.unlink(caminho_temporario)


def executar_com_lock(operacao=None):
    ARQUIVO_LOCK.touch(exist_ok=True)
    with ARQUIVO_LOCK.open("r+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        dados = ler_sem_lock()
        if operacao is not None:
            resultado = operacao(dados)
            salvar_sem_lock(dados)
            return resultado
        if not ARQUIVO_JSON.exists():
            salvar_sem_lock(dados)
        return dados


def registrar_historico(
    dados: dict, movimento: str, veiculo: dict, responsavel: str = "—"
) -> None:
    dados["historico"].append(
        {
            "data_hora": agora(),
            "movimento": movimento,
            "veiculo": veiculo["nome"],
            "id": veiculo["id"],
            "responsavel": responsavel or "—",
        }
    )


def adicionar_veiculo(veiculo_id: str, nome: str) -> tuple[bool, str]:
    veiculo_id = veiculo_id.strip().upper()
    nome = nome.strip()

    def operacao(dados):
        if any(v["id"].upper() == veiculo_id for v in dados["veiculos"]):
            return False, "Já existe um veículo com esse ID."
        veiculo = {"id": veiculo_id, "nome": nome, "responsavel": None}
        dados["veiculos"].append(veiculo)
        registrar_historico(dados, "Veículo adicionado", veiculo)
        return True, "Veículo adicionado."

    return executar_com_lock(operacao)


def editar_veiculo(
    veiculo_id_atual: str, novo_id: str, novo_nome: str
) -> tuple[bool, str]:
    novo_id = novo_id.strip().upper()
    novo_nome = novo_nome.strip()

    def operacao(dados):
        veiculo = next(
            v for v in dados["veiculos"] if v["id"] == veiculo_id_atual
        )
        if any(
            v["id"].upper() == novo_id and v["id"] != veiculo_id_atual
            for v in dados["veiculos"]
        ):
            return False, "Já existe outro veículo com esse ID."

        nome_anterior = veiculo["nome"]
        id_anterior = veiculo["id"]
        if nome_anterior == novo_nome and id_anterior == novo_id:
            return False, "Nenhuma alteração foi realizada."

        veiculo["nome"] = novo_nome
        veiculo["id"] = novo_id
        registrar_historico(
            dados,
            "Veículo editado",
            veiculo,
            f"{nome_anterior} ({id_anterior}) → {novo_nome} ({novo_id})",
        )
        return True, "Veículo atualizado."

    return executar_com_lock(operacao)


def retirar_veiculo(veiculo_id: str, responsavel: str) -> tuple[bool, str]:
    def operacao(dados):
        veiculo = next(v for v in dados["veiculos"] if v["id"] == veiculo_id)
        if veiculo.get("responsavel"):
            return False, "Este veículo acabou de ser retirado por outra pessoa."
        veiculo["responsavel"] = responsavel
        registrar_historico(dados, "Veículo retirado", veiculo, responsavel)
        return True, "Retirada registrada."

    return executar_com_lock(operacao)


def devolver_veiculo(veiculo_id: str) -> None:
    def operacao(dados):
        veiculo = next(v for v in dados["veiculos"] if v["id"] == veiculo_id)
        responsavel = veiculo.get("responsavel") or "—"
        veiculo["responsavel"] = None
        registrar_historico(dados, "Veículo devolvido", veiculo, responsavel)

    executar_com_lock(operacao)


def remover_veiculo(veiculo_id: str) -> tuple[bool, str]:
    def operacao(dados):
        veiculo = next(v for v in dados["veiculos"] if v["id"] == veiculo_id)
        if veiculo.get("responsavel"):
            return False, "Devolva o veículo antes de removê-lo."
        registrar_historico(dados, "Veículo removido", veiculo)
        dados["veiculos"].remove(veiculo)
        return True, "Veículo removido."

    return executar_com_lock(operacao)


def reordenar_veiculo(veiculo_id: str, nova_posicao: int) -> tuple[bool, str]:
    def operacao(dados):
        veiculos = dados["veiculos"]
        indice_atual = next(
            indice for indice, veiculo in enumerate(veiculos)
            if veiculo["id"] == veiculo_id
        )
        novo_indice = max(0, min(nova_posicao - 1, len(veiculos) - 1))
        if indice_atual == novo_indice:
            return False, "O veículo já está nessa posição."

        veiculo = veiculos.pop(indice_atual)
        veiculos.insert(novo_indice, veiculo)
        registrar_historico(
            dados,
            "Veículo reordenado",
            veiculo,
            f"Posição {indice_atual + 1} → {novo_indice + 1}",
        )
        return True, "Ordem atualizada."

    return executar_com_lock(operacao)


@st.dialog("Adicionar veículo", icon="➕")
def abrir_adicao() -> None:
    veiculo_id = st.text_input("Número ID", placeholder="Ex.: VEI-011")
    nome = st.text_input("Nome do veículo", placeholder="Ex.: Fiat Argo")
    if st.button("Adicionar veículo", type="primary", use_container_width=True):
        if not veiculo_id.strip() or not nome.strip():
            st.error("Preencha o ID e o nome do veículo.")
            return
        sucesso, mensagem = adicionar_veiculo(veiculo_id, nome)
        if sucesso:
            st.rerun()
        st.error(mensagem)


@st.dialog("Editar veículo", icon="✏️")
def abrir_edicao(veiculos: list[dict]) -> None:
    veiculo = st.selectbox(
        "Veículo para editar",
        options=veiculos,
        format_func=lambda v: f'{v["nome"]} — {v["id"]}',
        key="editar_selecao",
    )
    novo_id = st.text_input(
        "Número ID",
        value=veiculo["id"],
        key=f'editar_id_{veiculo["id"]}',
    )
    novo_nome = st.text_input(
        "Nome do veículo",
        value=veiculo["nome"],
        key=f'editar_nome_{veiculo["id"]}',
    )
    if st.button("Salvar alterações", type="primary", use_container_width=True):
        if not novo_id.strip() or not novo_nome.strip():
            st.error("Preencha o ID e o nome do veículo.")
            return
        sucesso, mensagem = editar_veiculo(
            veiculo["id"], novo_id, novo_nome
        )
        if sucesso:
            st.rerun()
        st.error(mensagem)


@st.dialog("Retirar veículo", icon="🚗")
def abrir_retirada(veiculo: dict) -> None:
    st.write(f'Você está retirando **{veiculo["nome"]}** — `{veiculo["id"]}`')
    nome = st.text_input(
        "Nome de quem vai pegar o veículo",
        placeholder="Digite o nome completo",
        key=f'nome_retirada_{veiculo["id"]}',
    )
    if st.button("Confirmar retirada", type="primary", use_container_width=True):
        nome = nome.strip()
        if not nome:
            st.error("Informe o nome da pessoa antes de confirmar.")
            return
        sucesso, mensagem = retirar_veiculo(veiculo["id"], nome)
        if sucesso:
            st.rerun()
        st.error(mensagem)


@st.dialog("Remover veículo", icon="🗑️")
def abrir_remocao(veiculo: dict) -> None:
    st.warning(
        f'Deseja remover **{veiculo["nome"]}** — `{veiculo["id"]}` da frota?'
    )
    st.caption("A remoção ficará registrada no histórico.")
    if st.button("Confirmar remoção", type="primary", use_container_width=True):
        sucesso, mensagem = remover_veiculo(veiculo["id"])
        if sucesso:
            st.rerun()
        st.error(mensagem)


@st.dialog("Reordenar veículos", icon="↕️")
def abrir_reordenacao(veiculos: list[dict]) -> None:
    veiculo = st.selectbox(
        "Veículo",
        options=veiculos,
        format_func=lambda v: f'{v["nome"]} — {v["id"]}',
        key="reordenar_veiculo",
    )
    posicao_atual = next(
        indice for indice, item in enumerate(veiculos, start=1)
        if item["id"] == veiculo["id"]
    )
    nova_posicao = st.number_input(
        "Nova posição",
        min_value=1,
        max_value=len(veiculos),
        value=posicao_atual,
        step=1,
    )
    st.caption(f"Posição atual: {posicao_atual} de {len(veiculos)}")
    if st.button("Salvar nova ordem", type="primary", use_container_width=True):
        sucesso, mensagem = reordenar_veiculo(veiculo["id"], int(nova_posicao))
        if sucesso:
            st.rerun()
        st.error(mensagem)


st.markdown(
    """
    <style>
        .stApp { background: #070b14; color: #f8fafc; }
        #MainMenu, header, footer { visibility: hidden; }
        .block-container { max-width: 1180px; padding-top: 2.5rem; padding-bottom: 3rem; }
        .cabecalho {
            padding: 1.8rem 2rem; margin-bottom: 1.2rem; color: white;
            border: 1px solid #263244; border-radius: 22px;
            background: linear-gradient(135deg, #111827, #1e293b);
            box-shadow: 0 14px 34px rgba(0, 0, 0, .35);
        }
        .cabecalho h1 { margin: 0; color: white; font-size: 2rem; }
        .cabecalho p { margin: 0.45rem 0 0; color: #94a3b8; }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: #263244; border-radius: 18px; background: #111827;
            box-shadow: 0 8px 24px rgba(0, 0, 0, .24);
        }
        .veiculo-topo { display: flex; align-items: center; gap: .7rem; margin-bottom: .85rem; }
        .status-dot {
            width: 15px; height: 15px; flex: 0 0 15px; border-radius: 50%;
            box-shadow: 0 0 0 5px var(--halo); background: var(--cor);
        }
        .veiculo-nome { color: #f8fafc; font-size: 1.12rem; font-weight: 750; }
        .veiculo-id { margin-bottom: .8rem; color: #94a3b8; font-size: .82rem; }
        .responsavel-label {
            color: #64748b; font-size: .76rem; font-weight: 700;
            letter-spacing: .06em; text-transform: uppercase;
        }
        .responsavel { min-height: 2.5rem; margin-top: .18rem; color: #f1f5f9; font-weight: 650; }
        .gestao-titulo {
            margin: 0 0 .35rem;
            color: #f8fafc !important;
            font-size: 1.7rem;
            font-weight: 800;
        }
        .gestao-descricao, .gestao-label {
            color: #cbd5e1 !important;
        }
        .gestao-descricao { margin: 0 0 1rem; }
        .gestao-label { margin: .9rem 0 .35rem; font-size: .9rem; font-weight: 650; }
        div[data-testid="stExpander"] summary p,
        div[data-testid="stExpander"] summary svg {
            color: #f8fafc !important;
            fill: #f8fafc !important;
        }
        .stButton > button { min-height: 42px; border-radius: 11px; font-weight: 700; }
        .stButton > button[kind="secondary"] {
            color: #e2e8f0; border: 1px solid #334155; background: #182235; box-shadow: none;
        }
        .stButton > button[kind="secondary"]:hover {
            color: #ffffff; border-color: #475569; background: #243146;
        }
        div[class*="st-key-pegar_"] button {
            color: #ffffff !important;
            border-color: #22c55e !important;
            background: #22c55e !important;
            box-shadow: 0 6px 16px rgba(34, 197, 94, .22) !important;
        }
        div[class*="st-key-pegar_"] button:hover {
            border-color: #16a34a !important;
            background: #16a34a !important;
        }
        div[class*="st-key-devolver_"] button {
            color: #ffffff !important;
            border-color: #ef4444 !important;
            background: #ef4444 !important;
            box-shadow: 0 6px 16px rgba(239, 68, 68, .22) !important;
        }
        div[class*="st-key-devolver_"] button:hover {
            border-color: #dc2626 !important;
            background: #dc2626 !important;
        }
        @media (max-width: 640px) {
            .block-container { padding: 1rem .8rem 2rem; }
            .cabecalho { padding: 1.35rem; }
            .cabecalho h1 { font-size: 1.55rem; }
            div[data-testid="stHorizontalBlock"] {
                display: flex;
                flex-wrap: nowrap;
                gap: .55rem;
            }
            div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
                min-width: 0;
                flex: 1 1 0;
                width: 50%;
            }
            div[data-testid="stVerticalBlockBorderWrapper"] {
                border-radius: 14px;
            }
            .veiculo-topo { gap: .45rem; margin-bottom: .5rem; }
            .status-dot { width: 11px; height: 11px; flex-basis: 11px; }
            .veiculo-nome { font-size: .93rem; }
            .veiculo-id { margin-bottom: .55rem; font-size: .7rem; }
            .responsavel-label { font-size: .62rem; letter-spacing: .03em; }
            .responsavel { min-height: 2rem; font-size: .82rem; }
            .stButton > button { min-height: 38px; padding: .35rem; font-size: .82rem; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="cabecalho">
        <h1>🚗 Controle de Veículos</h1>
    </section>
    """,
    unsafe_allow_html=True,
)

try:
    dados = executar_com_lock()
except Exception as erro:
    st.error("Não foi possível acessar o arquivo veiculos.json. Tente atualizar a página.")
    with st.expander("Detalhes técnicos"):
        st.code(str(erro))
    st.stop()

if st.button("↻ Atualizar status", type="secondary", use_container_width=True):
    st.rerun()

st.write("")

veiculos = dados["veiculos"]
if not veiculos:
    st.info("Nenhum veículo cadastrado. Use “Adicionar veículo” para começar.")

for inicio in range(0, len(veiculos), 2):
    colunas = st.columns(2)
    for coluna, veiculo in zip(colunas, veiculos[inicio : inicio + 2]):
        responsavel = veiculo.get("responsavel") or "Disponível"
        disponivel = responsavel == "Disponível"
        cor = "#22c55e" if disponivel else "#ef4444"
        halo = "rgba(34,197,94,.16)" if disponivel else "rgba(239,68,68,.16)"

        with coluna:
            with st.container(border=True):
                st.markdown(
                    f"""
                    <div class="veiculo-topo">
                        <span class="status-dot" style="--cor:{cor};--halo:{halo}"></span>
                        <span class="veiculo-nome">{html.escape(veiculo["nome"])}</span>
                    </div>
                    <div class="veiculo-id">ID: {html.escape(veiculo["id"])}</div>
                    <div class="responsavel-label">Responsável atual</div>
                    <div class="responsavel">{html.escape(responsavel)}</div>
                    """,
                    unsafe_allow_html=True,
                )
                if disponivel:
                    if st.button(
                        "Pegar", key=f'pegar_{veiculo["id"]}', type="primary",
                        use_container_width=True,
                    ):
                        abrir_retirada(veiculo)
                else:
                    if st.button(
                        "Devolver", key=f'devolver_{veiculo["id"]}',
                        type="secondary", use_container_width=True,
                    ):
                        devolver_veiculo(veiculo["id"])
                        st.rerun()

st.write("")
with st.expander(f'📋 Histórico de movimentações ({len(dados["historico"])})'):
    historico = list(reversed(dados["historico"]))
    if historico:
        st.dataframe(
            historico,
            column_order=["data_hora", "movimento", "veiculo", "id", "responsavel"],
            column_config={
                "data_hora": "Data e hora",
                "movimento": "Movimento",
                "veiculo": "Veículo",
                "id": "ID",
                "responsavel": "Responsável",
            },
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.caption("Nenhuma movimentação registrada.")

st.write("")
with st.container(border=True):
    st.markdown(
        """
        <h3 class="gestao-titulo">⚙️ Gestão da frota</h3>
        <p class="gestao-descricao">Adicione, remova, edite ou altere a ordem dos veículos.</p>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "＋ Adicionar veículo",
        key="gestao_adicionar",
        type="primary",
        use_container_width=True,
    ):
        abrir_adicao()

    disponiveis_para_remocao = [
        veiculo for veiculo in veiculos if not veiculo.get("responsavel")
    ]
    if disponiveis_para_remocao:
        st.markdown(
            '<p class="gestao-label">Veículo disponível para remoção</p>',
            unsafe_allow_html=True,
        )
        veiculo_selecionado = st.selectbox(
            "Veículo disponível para remoção",
            options=disponiveis_para_remocao,
            format_func=lambda v: f'{v["nome"]} — {v["id"]}',
            key="veiculo_para_remover",
            label_visibility="collapsed",
        )
        if st.button(
            "Remover veículo",
            key="gestao_remover",
            type="secondary",
            use_container_width=True,
        ):
            abrir_remocao(veiculo_selecionado)
    else:
        st.info("Não há veículos disponíveis para remoção.")

    if veiculos and st.button(
        "↕ Reordenar veículos",
        key="gestao_reordenar",
        type="secondary",
        use_container_width=True,
    ):
        abrir_reordenacao(veiculos)

    if veiculos and st.button(
        "✏️ Editar veículo",
        key="gestao_editar",
        type="secondary",
        use_container_width=True,
    ):
        abrir_edicao(veiculos)
