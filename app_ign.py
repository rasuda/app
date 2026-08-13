
import streamlit as st


st.set_page_config(
    page_title="Controle de Veículos",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# EDITE SOMENTE ESTA LISTA PARA ALTERAR A FROTA.
# Para incluir, adicione um item com ID único e nome.
# Para remover, apague o item. Para renomear, altere apenas "nome".
VEICULOS = [
    {"id": "VEI-001", "nome": "Veículo 01"},
    {"id": "VEI-002", "nome": "Veículo 02"},
    {"id": "VEI-003", "nome": "Veículo 03"},
    {"id": "VEI-004", "nome": "Veículo 04"},
    {"id": "VEI-005", "nome": "Veículo 05"},
    {"id": "VEI-006", "nome": "Veículo 06"},
    {"id": "VEI-007", "nome": "Veículo 07"},
    {"id": "VEI-008", "nome": "Veículo 08"},
    {"id": "VEI-009", "nome": "Veículo 09"},
    {"id": "VEI-010", "nome": "Veículo 10"},
]


if "emprestimos" not in st.session_state:
    st.session_state.emprestimos = {}

for veiculo in VEICULOS:
    st.session_state.emprestimos.setdefault(veiculo["id"], "Disponível")


@st.dialog("Retirar veículo", icon="🚗")
def abrir_retirada(veiculo: dict) -> None:
    st.write(f'Você está retirando **{veiculo["nome"]}** — `{veiculo["id"]}`')
    nome = st.text_input(
        "Nome de quem vai pegar o veículo",
        placeholder="Digite o nome completo",
        key=f'nome_retirada_{veiculo["id"]}',
    )

    if st.button("Confirmar retirada", type="primary", use_container_width=True):
        nome_limpo = nome.strip()
        if not nome_limpo:
            st.error("Informe o nome da pessoa antes de confirmar.")
        else:
            st.session_state.emprestimos[veiculo["id"]] = nome_limpo
            st.rerun()


def devolver(veiculo_id: str) -> None:
    st.session_state.emprestimos[veiculo_id] = "Disponível"


st.markdown(
    """
    <style>
        .stApp { background: #f4f7fb; }
        #MainMenu, header, footer { visibility: hidden; }
        .block-container {
            max-width: 1180px;
            padding-top: 2.5rem;
            padding-bottom: 3rem;
        }
        .cabecalho {
            padding: 1.8rem 2rem;
            margin-bottom: 1.4rem;
            color: white;
            border-radius: 22px;
            background: linear-gradient(135deg, #172033, #263b61);
            box-shadow: 0 14px 34px rgba(23, 32, 51, 0.18);
        }
        .cabecalho h1 { margin: 0; color: white; font-size: 2rem; }
        .cabecalho p { margin: 0.45rem 0 0; color: #cbd5e1; }
        div[data-testid="stMetric"] {
            padding: 1rem 1.2rem;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            background: white;
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: #e2e8f0;
            border-radius: 18px;
            background: white;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
        }
        .veiculo-topo {
            display: flex;
            align-items: center;
            gap: 0.7rem;
            margin-bottom: 0.85rem;
        }
        .status-dot {
            width: 15px;
            height: 15px;
            flex: 0 0 15px;
            border-radius: 50%;
            box-shadow: 0 0 0 5px var(--halo);
            background: var(--cor);
        }
        .veiculo-nome { color: #172033; font-size: 1.12rem; font-weight: 750; }
        .veiculo-id { margin-bottom: 0.8rem; color: #64748b; font-size: 0.82rem; }
        .responsavel-label {
            color: #94a3b8;
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }
        .responsavel {
            min-height: 2.5rem;
            margin-top: 0.18rem;
            color: #1e293b;
            font-size: 1rem;
            font-weight: 650;
        }
        .stButton > button { min-height: 42px; border-radius: 11px; font-weight: 700; }
        @media (max-width: 640px) {
            .block-container { padding: 1rem 0.8rem 2rem; }
            .cabecalho { padding: 1.35rem; }
            .cabecalho h1 { font-size: 1.55rem; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="cabecalho">
        <h1>🚗 Controle de Veículos</h1>
        <p>Gerencie a retirada e a devolução dos veículos da frota.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

total = len(VEICULOS)
disponiveis = sum(
    st.session_state.emprestimos[v["id"]] == "Disponível" for v in VEICULOS
)
emprestados = total - disponiveis

m1, m2, m3 = st.columns(3)
m1.metric("Total da frota", total)
m2.metric("Disponíveis", disponiveis)
m3.metric("Em uso", emprestados)

st.write("")

for inicio in range(0, len(VEICULOS), 2):
    colunas = st.columns(2)

    for coluna, veiculo in zip(colunas, VEICULOS[inicio : inicio + 2]):
        responsavel = st.session_state.emprestimos[veiculo["id"]]
        disponivel = responsavel == "Disponível"
        cor = "#22c55e" if disponivel else "#ef4444"
        halo = "rgba(34,197,94,.16)" if disponivel else "rgba(239,68,68,.16)"

        with coluna:
            with st.container(border=True):
                st.markdown(
                    f"""
                    <div class="veiculo-topo">
                        <span class="status-dot" style="--cor:{cor};--halo:{halo}"></span>
                        <span class="veiculo-nome">{veiculo["nome"]}</span>
                    </div>
                    <div class="veiculo-id">ID: {veiculo["id"]}</div>
                    <div class="responsavel-label">Responsável atual</div>
                    <div class="responsavel">{responsavel}</div>
                    """,
                    unsafe_allow_html=True,
                )

                botao_pegar, botao_devolver = st.columns(2)
                with botao_pegar:
                    if st.button(
                        "Pegar",
                        key=f'pegar_{veiculo["id"]}',
                        type="primary",
                        disabled=not disponivel,
                        use_container_width=True,
                    ):
                        abrir_retirada(veiculo)

                with botao_devolver:
                    st.button(
                        "Devolver",
                        key=f'devolver_{veiculo["id"]}',
                        on_click=devolver,
                        args=(veiculo["id"],),
                        disabled=disponivel,
                        use_container_width=True,
                    )


