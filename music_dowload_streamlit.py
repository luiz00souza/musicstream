import os
import streamlit as st
import streamlit.components.v1 as components
import yt_dlp

# Configuração da página
st.set_page_config(
    page_title="SpotPy - Continuous Streaming", 
    page_icon="🎵", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ESTILIZAÇÃO CSS (SPOTIFY STYLE) ---
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    h1 { color: #1DB954 !important; font-family: 'Circular', sans-serif; font-weight: 800; margin-bottom: 0px;}
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
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        background-color: #222222 !important;
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
    .btn-secondary button:hover { background-color: #3e3e3e !important; border-color: #FFFFFF !important; }
    
    /* Tag indicando a origem da recomendação */
    .priority-badge {
        font-size: 0.7rem;
        font-weight: bold;
        padding: 2px 6px;
        border-radius: 4px;
        margin-bottom: 5px;
        display: inline-block;
    }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DOS ESTADOS DE SESSÃO ---
if 'current_track' not in st.session_state:
    st.session_state.current_track = None
if 'queue' not in st.session_state:
    st.session_state.queue = []
if 'history' not in st.session_state:
    st.session_state.history = []

# --- MOTOR DE RECOMENDAÇÃO HIERÁRQUICO COM PRIORIDADES ---
# --- MOTOR DE RECOMENDAÇÃO HIERÁRQUICO CORRIGIDO (ARTISTA != CANAL) ---
def buscar_musicas_hierarquicas(track, num_resultados=4):
    filtradas = []
    nomes_bloqueados = [track['title']] + [t['title'] for t in st.session_state.queue]
    ydl_opts = {'format': 'bestaudio[ext=m4a]/bestaudio', 'extract_flat': False, 'skip_download': True}
    
    # --- ENGENHARIA DE EXTRAÇÃO DE ARTISTA ---
    # Se o título for "Falamansa - Xote dos Milagres", isolamos "Falamansa"
    titulo_original = track['title']
    nome_artista = track['uploader'] # Fallback inicial
    
    if " - " in titulo_original:
        nome_artista = titulo_original.split(" - ")[0].strip()
    elif " – " in titulo_original: # Travessão longo comum
        nome_artista = titulo_original.split(" – ")[0].strip()
    
    # Remove termos comuns de canais para limpar o nome do artista
    termos_limpeza = [" - Topic", " Oficial", " Official", " VEVO", " Tema"]
    for termo in termos_limpeza:
        nome_artista = nome_artista.replace(termo, "")
    nome_artista = nome_artista.strip()

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # --- PRIORIDADE 1: MESMO ÁLBUM ---
        try:
            # Buscamos combinando o Artista Real + o nome da música para caçar o álbum completo
            query_album = f"{nome_artista} {titulo_original} album completo"
            info_album = ydl.extract_info(f"ytsearch4:{query_album}", download=False)
            if 'entries' in info_album:
                for entry in info_album['entries']:
                    if entry.get('title') not in nomes_bloqueados and len(filtradas) < num_resultados:
                        filtradas.append({
                            'title': entry.get('title'), 'url': entry.get('webpage_url'), 'stream_url': entry.get('url'),
                            'uploader': entry.get('uploader'), 'duration': entry.get('duration_string'), 'id': entry.get('id'),
                            'tag': '💿 MESMO ÁLBUM', 'tag_color': '#4A90E2'
                        })
                        nomes_bloqueados.append(entry.get('title'))
        except:
            pass

        # --- PRIORIDADE 2: MESMO ARTISTA REAL (Não o canal) ---
        if len(filtradas) < num_resultados:
            try:
                # Agora a busca é focada na obra do artista extraído
                query_artista = f"{nome_artista} top musicas"
                info_artista = ydl.extract_info(f"ytsearch5:{query_artista}", download=False)
                if 'entries' in info_artista:
                    for entry in info_artista['entries']:
                        if entry.get('title') not in nomes_bloqueados and len(filtradas) < num_resultados:
                            filtradas.append({
                                'title': entry.get('title'), 'url': entry.get('webpage_url'), 'stream_url': entry.get('url'),
                                'uploader': entry.get('uploader'), 'duration': entry.get('duration_string'), 'id': entry.get('id'),
                                'tag': '👤 MESMO ARTISTA', 'tag_color': '#1DB954'
                            })
                            nomes_bloqueados.append(entry.get('title'))
            except:
                pass

        # --- PRIORIDADE 3: MESMA PLAYLIST / MIX ---
        if len(filtradas) < num_resultados:
            try:
                query_mix = f"{titulo_original} mix musicas semelhantes"
                info_mix = ydl.extract_info(f"ytsearch5:{query_mix}", download=False)
                if 'entries' in info_mix:
                    for entry in info_mix['entries']:
                        if entry.get('title') not in nomes_bloqueados and len(filtradas) < num_resultados:
                            filtradas.append({
                                'title': entry.get('title'), 'url': entry.get('webpage_url'), 'stream_url': entry.get('url'),
                                'uploader': entry.get('uploader'), 'duration': entry.get('duration_string'), 'id': entry.get('id'),
                                'tag': '🎶 MIX / PLAYLIST', 'tag_color': '#7D3CFF'
                            })
                            nomes_bloqueados.append(entry.get('title'))
            except:
                pass
                
    return filtradas

def tocar_faixa(track):
    if st.session_state.current_track:
        st.session_state.history.append(st.session_state.current_track)
    st.session_state.current_track = track
    
    with st.spinner("Analisando prioridades de reprodução..."):
        novas_similares = buscar_musicas_hierarquicas(track)
    st.session_state.queue = novas_similares
    st.rerun()

def avancar_fila():
    if st.session_state.queue:
        proxima = st.session_state.queue.pop(0)
        tocar_faixa(proxima)
    else:
        st.toast("Fim da playlist automática.", icon="🛑")

# --- INTERFACE ---
st.title("🎵 SpotPy: Infinite Radio Mode")
st.caption("Streaming contínuo estruturado por prioridade de Álbum, Artista e Playlist.")
st.write("---")

search_query = st.text_input("", placeholder="Digite uma música ou artista para iniciar a rádio...", label_visibility="collapsed")

if search_query:
    if 'last_main_query' not in st.session_state or st.session_state.last_main_query != search_query:
        with st.spinner("Sintonizando frequências..."):
            ydl_opts_main = {'format': 'bestaudio[ext=m4a]/bestaudio', 'extract_flat': False, 'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts_main) as ydl:
                info_main = ydl.extract_info(f"ytsearch3:{search_query}", download=False)
            if 'entries' in info_main and len(info_main['entries']) > 0:
                st.session_state.main_search_results = [{
                    'title': e.get('title'), 'url': e.get('webpage_url'), 'stream_url': e.get('url'),
                    'uploader': e.get('uploader'), 'duration': e.get('duration_string'), 'id': e.get('id')
                } for e in info_main['entries']]
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

# --- PAINEL DO PLAYER DE ÁUDIO AVANÇADO ---
if st.session_state.current_track:
    st.write("---")
    
    col_player_left, col_queue_right = st.columns([6, 4])
    
    with col_player_left:
        st.markdown(f"""
            <div class="now-playing-box">
                <span style="color: #1DB954; font-size: 0.8rem; font-weight: bold; letter-spacing: 2px;">TOCANDO AGORA VIA STREAMING</span>
                <h2 style="margin-top: 5px; margin-bottom: 5px; font-size: 1.8rem;">{st.session_state.current_track['title']}</h2>
                <span style="color: #B3B3B3;">Canal original: {st.session_state.current_track['uploader']} | Duração: {st.session_state.current_track['duration']}</span>
            </div>
        """, unsafe_allow_html=True)
        
        # --- INJEÇÃO HTML5 + JAVASCRIPT: AUTOPLAY & FADE OUT ---
        src_audio = st.session_state.current_track['stream_url']
        
        js_player_component = f"""
        <div style="background-color: #181818; padding: 15px; border-radius: 30px; display: flex; align-items: center; justify-content: center;">
            <audio id="audio-player" src="{src_audio}" controls autoplay style="width: 100%; border-radius: 30px; height: 40px;"></audio>
        </div>

        <script>
            const audio = document.getElementById('audio-player');
            let fadeTriggered = false;

            audio.addEventListener('timeupdate', () => {{
                const timeLeft = audio.duration - audio.currentTime;
                if (timeLeft <= 4 && !fadeTriggered && audio.duration > 0) {{
                    fadeTriggered = true;
                    fadeVolumeOut(audio);
                }}
            }});

            function fadeVolumeOut(player) {{
                let volume = player.volume;
                const interval = setInterval(() => {{
                    if (volume > 0.05) {{
                        volume -= 0.05;
                        player.volume = volume;
                    }} else {{
                        player.volume = 0;
                        clearInterval(interval);
                        window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'NEXT_TRACK'}}, '*');
                    }}
                }}, 200);
            }}
        </script>
        """
        
        components.html(js_player_component, height=90)
        
        # Controles Manuais Alternativos
        st.write("")
        c1, c2, c3 = st.columns([2, 8, 2])
        with c2:
            if st.session_state.queue:
                texto_proxima = f"Avançar para: {st.session_state.queue[0]['title'][:35]}..."
            else:
                texto_proxima = "Fim da Fila"
                
            st.markdown('<div class="btn-secondary">', unsafe_allow_html=True)
            if st.button(f"⏭️ {texto_proxima}", use_container_width=True, disabled=not st.session_state.queue):
                avancar_fila()
            st.markdown('</div>', unsafe_allow_html=True)

    # COLUNA 2: A FILA DINÂMICA COM OS LABELS DE PRIORIDADE
    with col_queue_right:
        st.subheader("⏭️ A Seguir (Ordem de Afinidade)")
        
        if st.session_state.queue:
            for q_idx, q_track in enumerate(st.session_state.queue):
                with st.container(border=True):
                    col_q_info, col_q_play = st.columns([8, 2])
                    with col_q_info:
                        # Emite o badge colorido baseado no tipo de prioridade alcançada
                        st.markdown(f'<span class="priority-badge" style="background-color: {q_track["tag_color"]};">{q_track["tag"]}</span>', unsafe_allow_html=True)
                        st.markdown(f"**{q_track['title'][:45]}...**" if len(q_track['title']) > 45 else f"**{q_track['title']}**")
                        st.caption(f"{q_track['uploader']} • {q_track['duration']}")
                    with col_q_play:
                        if st.button("▶️", key=f"play_q_{q_track['id']}_{q_idx}"):
                            st.session_state.queue.pop(q_idx)
                            tocar_faixa(q_track)
        else:
            st.write("Fila vazia.")
