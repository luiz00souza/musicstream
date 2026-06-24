import os
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import yt_dlp
import time

# Configuração da página
st.set_page_config(
    page_title="SpotPy - Real Continuous Streaming", 
    page_icon="🎵", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ESTILIZAÇÃO CSS (SPOTIFY STYLE) ---
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    h1 { color: #1DB954 !important; font-family: 'Circular', sans-serif; font-weight: 800; }
    h2, h3 { color: #FFFFFF !important; font-family: 'Circular', sans-serif; }
    
    .now-playing-box {
        background: linear-gradient(135deg, #1e1e1e 0%, #282828 100%);
        border: 1px solid #1DB954;
        border-radius: 12px;
        padding: 25px;
        margin-bottom: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #181818 !important;
        border: 1px solid #282828 !important;
        border-radius: 8px !important;
        padding: 15px !important;
    }
    
    .stTextInput input {
        background-color: #2A2A2A !important;
        color: #FFFFFF !important;
        border-radius: 50px !important;
        padding-left: 20px !important;
    }
    .stButton button {
        background-color: #1DB954 !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        border-radius: 50px !important;
        border: none !important;
    }
    .stButton button:hover { background-color: #1ED760 !important; }
    
    .btn-secondary button {
        background-color: #282828 !important;
        color: #FFFFFF !important;
        border: 1px solid #727272 !important;
    }
    audio { border-radius: 30px; height: 45px; width: 100%; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DOS ESTADOS DE SESSÃO ---
if 'current_track' not in st.session_state:
    st.session_state.current_track = None
if 'queue' not in st.session_state:
    st.session_state.queue = []
if 'track_start_time' not in st.session_state:
    st.session_state.track_start_time = 0
if 'track_duration_secs' not in st.session_state:
    st.session_state.track_duration_secs = 0

# --- MOTOR DE RECOMENDAÇÃO CONTÍNUA ---
def buscar_musicas_similares(termo_referencia, num_resultados=4):
    try:
        query = f"{termo_referencia} mix musicas semelhantes"
        ydl_opts = {'format': 'bestaudio[ext=m4a]/bestaudio', 'extract_flat': False, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch6:{query}", download=False)
            
        if 'entries' in info and len(info['entries']) > 0:
            filtradas = []
            nomes_bloqueados = [st.session_state.current_track['title']] if st.session_state.current_track else []
            nomes_bloqueados += [t['title'] for t in st.session_state.queue]
            
            for entry in info['entries']:
                if entry.get('title') not in nomes_bloqueados:
                    # Converte a duração para segundos (ex: "3:45" -> 225)
                    duration_str = entry.get('duration_string', '3:00')
                    parts = list(map(int, duration_str.split(':')))
                    secs = parts[0]*60 + parts[1] if len(parts) == 2 else parts[0]*3600 + parts[1]*60 + parts[2]
                    
                    filtradas.append({
                        'title': entry.get('title'),
                        'url': entry.get('webpage_url'),
                        'stream_url': entry.get('url'),
                        'uploader': entry.get('uploader'),
                        'duration': duration_str,
                        'duration_secs': secs,
                        'id': entry.get('id')
                    })
                if len(filtradas) >= num_resultados:
                    break
            return filtradas
    except:
        return []
    return []

def tocar_faixa(track):
    st.session_state.current_track = track
    st.session_state.track_start_time = time.time()
    st.session_state.track_duration_secs = track.get('duration_secs', 180)
    
    # Busca as próximas da rádio
    with st.spinner("Sintonizando próximas faixas da rádio..."):
        st.session_state.queue = buscar_musicas_similares(track['title'])
    st.rerun()

def avancar_fila():
    if st.session_state.queue:
        proxima = st.session_state.queue.pop(0)
        tocar_faixa(proxima)
    else:
        st.session_state.current_track = None
        st.toast("Fim da rádio automática.", icon="🛑")
        st.rerun()

# --- ATRAVESSADOR DE FILA AUTOMÁTICO (AUTOPLAY CONTROL) ---
# Se tem uma música tocando, ativa o atualizador a cada 3 segundos
if st.session_state.current_track:
    st_autorefresh(interval=3000, key="track_timer")
    
    # Calcula quanto tempo passou desde o play
    tempo_decorrido = time.time() - st.session_state.track_start_time
    tempo_restante = st.session_state.track_duration_secs - tempo_decorrido
    
    # GATILHO DE AUTOPLAY: Se faltar menos de 2 segundos para acabar, passa para a próxima
    if tempo_restante <= 2:
        avancar_fila()

# --- INTERFACE GRAPHICA ---
st.title("🎵 SpotPy: Infinite Radio Mode")
st.caption("Modo rádio contínuo com transição garantida pelo servidor.")
st.write("---")

search_query = st.text_input("", placeholder="Digite uma combinação (Ex: zouk x forro) para iniciar...", label_visibility="collapsed")

if search_query:
    if 'last_main_query' not in st.session_state or st.session_state.last_main_query != search_query:
        with st.spinner("Buscando pontos de partida..."):
            ydl_opts_main = {'format': 'bestaudio[ext=m4a]/bestaudio', 'extract_flat': False, 'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts_main) as ydl:
                info_main = ydl.extract_info(f"ytsearch3:{search_query}", download=False)
            if 'entries' in info_main and len(info_main['entries']) > 0:
                results = []
                for e in info_main['entries']:
                    d_str = e.get('duration_string', '3:00')
                    pts = list(map(int, d_str.split(':')))
                    s = pts[0]*60 + pts[1] if len(pts) == 2 else 180
                    results.append({
                        'title': e.get('title'), 'url': e.get('webpage_url'), 'stream_url': e.get('url'),
                        'uploader': e.get('uploader'), 'duration': d_str, 'duration_secs': s, 'id': e.get('id')
                    })
                st.session_state.main_search_results = results
                st.session_state.last_main_query = search_query

    if 'main_search_results' in st.session_state:
        st.subheader("🎯 Escolha o ponto de partida:")
        cols_start = st.columns(3)
        for idx, track in enumerate(st.session_state.main_search_results):
            with cols_start[idx]:
                with st.container(border=True):
                    st.markdown(f"**{track['title'][:60]}...**" if len(track['title']) > 60 else f"**{track['title']}**")
                    st.caption(f"{track['uploader']} • {track['duration']}")
                    if st.button("Iniciar Rádio aqui 📻", key=f"start_{track['id']}", use_container_width=True):
                        tocar_faixa(track)

# --- PANEL DE CONTROLE ---
if st.session_state.current_track:
    st.write("---")
    col_player_left, col_queue_right = st.columns([6, 4])
    
    with col_player_left:
        # Mostra barra de progresso aproximada
        elapsed = min(time.time() - st.session_state.track_start_time, st.session_state.track_duration_secs)
        pct = elapsed / st.session_state.track_duration_secs
        
        st.markdown(f"""
            <div class="now-playing-box">
                <span style="color: #1DB954; font-size: 0.8rem; font-weight: bold; letter-spacing: 2px;">RÁDIO ATIVA VIA STREAMING</span>
                <h2 style="margin-top: 5px; margin-bottom: 5px; font-size: 1.6rem;">{st.session_state.current_track['title']}</h2>
                <span style="color: #B3B3B3;">{st.session_state.current_track['uploader']}</span>
            </div>
        """, unsafe_allow_html=True)
        
        # Player nativo estável
        st.audio(st.session_state.current_track['stream_url'], format="audio/mp4", autoplay=True)
        st.progress(pct, text=f"Progresso da faixa: {int(elapsed)//60}:{int(elapsed)%60:02d} / {st.session_state.current_track['duration']}")
        
        # Botão manual de Skip
        st.write("")
        if st.session_state.queue:
            texto_proxima = f"Avançar para: {st.session_state.queue[0]['title'][:30]}..."
        else:
            texto_proxima = "Fim da Fila"
            
        st.markdown('<div class="btn-secondary">', unsafe_allow_html=True)
        if st.button(f"⏭️ {texto_proxima}", use_container_width=True, disabled=not st.session_state.queue):
            avancar_fila()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_queue_right:
        st.subheader("⏭️ Próximas da Rádio Composta")
        if st.session_state.queue:
            for q_idx, q_track in enumerate(st.session_state.queue):
                with st.container(border=True):
                    col_q_info, col_q_play = st.columns([8, 2])
                    with col_q_info:
                        st.markdown(f"**{q_track['title'][:45]}...**")
                        st.caption(f"{q_track['uploader']} • {q_track['duration']}")
                    with col_q_play:
                        if st.button("▶️", key=f"play_q_{q_track['id']}_{q_idx}"):
                            st.session_state.queue.pop(q_idx)
                            tocar_faixa(q_track)
        else:
            st.write("Mapeando contexto...")
