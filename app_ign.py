import streamlit as st


st.set_page_config(
    page_title="Controle IGN",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed",
)

if "ign_ligada" not in st.session_state:
    st.session_state.ign_ligada = False


def alternar_ign() -> None:
    """Alterna apenas o estado visual da IGN."""
    st.session_state.ign_ligada = not st.session_state.ign_ligada


ligada = st.session_state.ign_ligada
cor_status = "#35e07a" if ligada else "#ff4b55"
cor_suave = "rgba(53, 224, 122, 0.18)" if ligada else "rgba(255, 75, 85, 0.18)"
texto_status = "LIGADA" if ligada else "DESLIGADA"
icone_status = "⚡" if ligada else "○"

st.markdown(
    f"""
    <style>
        .stApp {{
            background:
                radial-gradient(circle at 50% 15%, #253044 0%, #111827 42%, #080d16 100%);
            color: #f8fafc;
        }}

        #MainMenu, header, footer {{ visibility: hidden; }}

        .block-container {{
            max-width: 620px;
            padding-top: 8vh;
        }}

        .painel {{
            padding: 38px 34px 30px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 28px;
            background: rgba(14, 22, 36, 0.86);
            box-shadow: 0 26px 70px rgba(0, 0, 0, 0.42);
            backdrop-filter: blur(16px);
        }}

        .titulo {{
            margin: 0;
            color: #f8fafc;
            font-size: 1.8rem;
            font-weight: 750;
            letter-spacing: -0.03em;
        }}

        .subtitulo {{
            margin: 7px 0 30px;
            color: #94a3b8;
            font-size: 0.95rem;
        }}

        .indicador {{
            width: 166px;
            height: 166px;
            margin: 0 auto 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 2px solid {cor_status};
            border-radius: 50%;
            color: {cor_status};
            font-size: 4.1rem;
            background: {cor_suave};
            box-shadow: 0 0 36px {cor_suave}, inset 0 0 28px rgba(0, 0, 0, 0.35);
        }}

        .estado {{
            margin-bottom: 28px;
            color: {cor_status};
            font-size: 1.1rem;
            font-weight: 800;
            letter-spacing: 0.16em;
        }}

        .stButton > button {{
            width: 100%;
            min-height: 58px;
            border: 1px solid {cor_status};
            border-radius: 16px;
            color: #ffffff;
            background: {cor_status};
            font-size: 1rem;
            font-weight: 800;
            box-shadow: 0 10px 28px {cor_suave};
            transition: transform 0.15s ease, filter 0.15s ease;
        }}

        .stButton > button:hover {{
            border-color: {cor_status};
            color: #ffffff;
            filter: brightness(1.08);
            transform: translateY(-1px);
        }}

        .stButton > button:focus {{
            color: #ffffff;
            box-shadow: 0 0 0 4px {cor_suave};
        }}

        .aviso {{
            margin-top: 22px;
            color: #64748b;
            font-size: 0.78rem;
        }}
    </style>

    <div class="painel">
        <p class="titulo">Controle de Ignição</p>
        <p class="subtitulo">Interface de controle da IGN</p>
        <div class="indicador">{icone_status}</div>
        <div class="estado">IGN {texto_status}</div>
    """,
    unsafe_allow_html=True,
)

st.button(
    "DESLIGAR IGN" if ligada else "LIGAR IGN",
    on_click=alternar_ign,
    use_container_width=True,
    type="primary",
)

st.markdown(
    """
        <div class="aviso">PROTÓTIPO DE INTERFACE • SEM CONEXÃO COM HARDWARE</div>
    </div>
    """,
    unsafe_allow_html=True,
)
