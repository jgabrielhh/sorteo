import streamlit as st
import pandas as pd
import random
import os
import json
import time

st.set_page_config(
    page_title="Sorteo App",
    page_icon="🥳🎉",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_DIR = 'data'
STATE_FILE = os.path.join(DATA_DIR, 'state.json')
UPLOADS_DIR = 'uploads'
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

DEFAULT_STATE = {
    'title': 'Sorteo',
    'participants': [],
    'prizes': [],
    'total_turns': 1,
    'current_turn': 1,
    'winners_history': [],
    'available_participants': [],
    'available_prizes': []
}

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return DEFAULT_STATE.copy()
    return DEFAULT_STATE.copy()

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def reset_state():
    save_state(DEFAULT_STATE.copy())
    st.session_state.state = DEFAULT_STATE.copy()
    st.rerun()

if 'state' not in st.session_state:
    st.session_state.state = load_state()

def update_state():
    save_state(st.session_state.state)

if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'setup'

if 'current_winners' not in st.session_state:
    st.session_state.current_winners = []

if 'animation_done' not in st.session_state:
    st.session_state.animation_done = False

def parse_uploaded_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            return df.iloc[:, 0].dropna().astype(str).tolist()
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
            return df.iloc[:, 0].dropna().astype(str).tolist()
        elif uploaded_file.name.endswith('.txt'):
            content = uploaded_file.read().decode('utf-8')
            return [line.strip() for line in content.splitlines() if line.strip()]
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return []
    return []

@st.dialog("Agregar Participantes Extra")
def add_participants_modal():
    uploaded_file = st.file_uploader("Subir CSV/Excel/Txt", type=['csv', 'xlsx', 'txt'], key="modal_parts_upload")
    if st.button("Cargar Participantes"):
        if uploaded_file:
            new_items = parse_uploaded_file(uploaded_file)
            if new_items:
                st.session_state.state['participants'].extend(new_items)
                st.session_state.state['available_participants'].extend(new_items)
                update_state()
                st.success(f"✅ Se agregaron {len(new_items)} participantes.")
                time.sleep(1)
                st.rerun()
        else:
            st.error("Por favor, sube un archivo primero.")

@st.dialog("Agregar Premios Extra")
def add_prizes_modal():
    uploaded_file = st.file_uploader("Subir CSV/Excel/Txt", type=['csv', 'xlsx', 'txt'], key="modal_prizes_upload")
    if st.button("Cargar Premios"):
        if uploaded_file:
            new_items = parse_uploaded_file(uploaded_file)
            if new_items:
                st.session_state.state['prizes'].extend(new_items)
                st.session_state.state['available_prizes'].extend(new_items)
                update_state()
                st.success(f"✅ Se agregaron {len(new_items)} premios.")
                time.sleep(1)
                st.rerun()
        else:
            st.error("Por favor, sube un archivo primero.")

def render_setup():
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        new_title = st.text_input("Título del Sorteo", value=st.session_state.state.get('title', 'Sorteo'))
        if new_title != st.session_state.state['title']:
            st.session_state.state['title'] = new_title
            update_state()
            st.rerun()

        st.subheader("Subir Datos")
        
        uploaded_participants = st.file_uploader("Cargar Participantes", type=['csv', 'xlsx', 'txt'], key="part_upload")
        if uploaded_participants:
            items = parse_uploaded_file(uploaded_participants)
            if items:
                if items != st.session_state.state['participants']:
                    st.session_state.state['participants'] = items
                    st.session_state.state['available_participants'] = items.copy()
                    st.session_state.state['winners_history'] = []
                    st.session_state.state['current_turn'] = 1
                    update_state()
                    st.success(f"✅ {len(items)} participantes cargados.")

        uploaded_prizes = st.file_uploader("Cargar Premios (Opcional)", type=['csv', 'xlsx', 'txt'], key="prize_upload")
        if uploaded_prizes:
            items = parse_uploaded_file(uploaded_prizes)
            if items:
                if items != st.session_state.state['prizes']:
                    st.session_state.state['prizes'] = items
                    st.session_state.state['available_prizes'] = items.copy()
                    update_state()
                    st.success(f"✅ {len(items)} premios cargados.")

        st.divider()
        if st.button("🔄 Reiniciar Todo", type="primary"):
            reset_state()
            st.rerun()

    st.title(st.session_state.state['title'])

    tab1, tab2, tab3, tab4 = st.tabs(["🎲 Sorteo", "👥 Participantes", "🏆 Premios", "📜 Historial"])

    with tab1:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Configurar Turno")
            winners_count = st.number_input("Ganadores en este turno", min_value=1, value=1)
            
            avail_part = len(st.session_state.state['available_participants'])
            avail_prize = len(st.session_state.state['available_prizes'])
            
            st.info(f"Participantes disponibles: **{avail_part}**")
            if st.session_state.state['prizes']:
                st.info(f"Premios disponibles: **{avail_prize}**")
            
            can_run = True
            if winners_count > avail_part:
                st.error("⚠️ No hay suficientes participantes.")
                can_run = False
            if st.session_state.state['prizes'] and winners_count > avail_prize:
                st.warning("⚠️ No hay suficientes premios.")
                can_run = False

            c_ext1, c_ext2 = st.columns(2)
            with c_ext1:
                if st.button("➕ Part. Extra", use_container_width=True):
                    add_participants_modal()
            with c_ext2:
                if st.button("➕ Premios Extra", use_container_width=True):
                    add_prizes_modal()
            
            st.divider()


            if st.button("🎰 SORTEAR!", disabled=not can_run, type="primary", use_container_width=True):
                st.session_state.winners_count_setting = winners_count
                st.session_state.view_mode = 'raffle'
                st.session_state.animation_done = False
                st.rerun()

        with col2:
            st.subheader("🎉 Últimos Ganadores")
            if st.session_state.state['winners_history']:
                last_turn = st.session_state.state['winners_history'][-1]
                st.markdown(f"### Turno {last_turn['turn']}")
                for res in last_turn['results']:
                    with st.container(border=True):
                        c1, c2 = st.columns(2)
                        c1.metric("Ganador", res['winner'])
                        c2.metric("Premio", res['prize'])
            else:
                st.info("Aún no se ha realizado ningún sorteo.")

    with tab2:
        st.dataframe(pd.DataFrame(st.session_state.state['participants'], columns=["Nombre"]), use_container_width=True)

    with tab3:
        if st.session_state.state['prizes']:
            st.dataframe(pd.DataFrame(st.session_state.state['prizes'], columns=["Premio"]), use_container_width=True)
        else:
            st.info("No hay premios cargados.")

    with tab4:
        if st.session_state.state['winners_history']:
            history_data = []
            for turn in st.session_state.state['winners_history']:
                for res in turn['results']:
                    history_data.append({
                        "Turno": turn['turn'],
                        "Ganador": res['winner'],
                        "Premio": res['prize']
                    })
            df_hist = pd.DataFrame(history_data)
            st.dataframe(df_hist, use_container_width=True)
            csv = df_hist.to_csv(index=False).encode('utf-8')
            st.download_button(label="💾 Descargar Resultados (CSV)", data=csv, file_name="resultados_sorteo.csv", mime="text/csv")
        else:
            st.info("Historial vacío.")


def render_raffle():
    st.markdown("""
    <style>
        .stApp {
            background-color: #000000;
        }
        .countdown {
            font-size: 15rem;
            color: #ff0055;
            font-weight: 900;
            text-align: center;
            animation: pulse 0.8s infinite;
        }
        .text-search {
            font-family: monospace;
            color: #00d4ff;
            font-size: 3rem;
            text-align: center;
        }
        .winner-card {
            background: linear-gradient(135deg, #1f1f1f 0%, #333 100%);
            padding: 40px;
            border-radius: 20px;
            border: 2px solid #00d4ff;
            text-align: center;
            margin: 20px auto;
            max-width: 600px;
            box-shadow: 0 0 50px rgba(0, 212, 255, 0.5);
            animation: popIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        .winner-name {
            font-size: 3.5rem;
            color: white;
            font-weight: bold;
            text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
        }
        .winner-prize {
            font-size: 1.8rem;
            color: #ffd700;
            margin-top: 10px;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.1); opacity: 0.8; }
            100% { transform: scale(1); opacity: 1; }
        }
        @keyframes popIn {
            from { transform: scale(0.5); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }
    </style>
    """, unsafe_allow_html=True)

    container = st.empty()

    if not st.session_state.animation_done:
        winners_count = st.session_state.winners_count_setting
        winners = random.sample(st.session_state.state['available_participants'], winners_count)
        
        current_prizes = []
        if st.session_state.state['available_prizes']:
             current_prizes = st.session_state.state['available_prizes'][:winners_count]
        
        results = []
        for i, w in enumerate(winners):
            pz = current_prizes[i] if i < len(current_prizes) else "Premio Sorpresa"
            results.append({'winner': w, 'prize': pz})
            st.session_state.state['available_participants'].remove(w)
            if i < len(current_prizes):
                st.session_state.state['available_prizes'].remove(pz)
        
        st.session_state.state['winners_history'].append({
            'turn': st.session_state.state['current_turn'],
            'results': results
        })
        st.session_state.state['current_turn'] += 1
        update_state()
        st.session_state.current_winners = results


        for i in range(3, 0, -1):
            container.markdown(f"<div class='countdown'>{i}</div>", unsafe_allow_html=True)
            time.sleep(1)
        
        for _ in range(10):
            container.markdown(f"<div class='text-search'>{random.choice(['BUSCANDO...', 'ALEATORIO...', 'ESCANEO...', 'MEMEZCLANDO...'])}</div>", unsafe_allow_html=True)
            time.sleep(0.1)
        
        container.empty()
        st.session_state.animation_done = True
        st.balloons()
        st.rerun()

    else:
        st.markdown("<h1 style='text-align: center; color: white;'>🎉 ¡FELICIDADES! 🎉</h1>", unsafe_allow_html=True)
        
        for res in st.session_state.current_winners:
            st.markdown(f"""
            <div class='winner-card'>
                <div class='winner-name'>{res['winner']}</div>
                <div class='winner-prize'>🏆 {res['prize']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("⬅️ Volver al Sorteo", use_container_width=True):
                st.session_state.view_mode = 'setup'
                st.session_state.animation_done = False
                st.rerun()

if st.session_state.view_mode == 'setup':
    render_setup()
elif st.session_state.view_mode == 'raffle':
    render_raffle()
