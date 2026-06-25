import os
import time
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
import yt_dlp

# --- CONFIGURAÇÃO DA PÁGINA ---
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
        color: #FFFFFF;
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
if 'track_start_time' not in st.session_state:
    st.session_state.track_start_time = 0
if 'track_duration_secs' not in st.session_state:
    st.session_state.track_duration_secs = 0

# --- FUNÇÃO AUXILIAR DE CONVERSÃO DE TEMPO ---
def converter_duracao_segundos(duration_str):
    try:
        if not duration_str:
            return 180
        parts = list(map(int, duration_str.split(':')))
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        return int(duration_str)
    except:
        return 180

# --- MOTOR DE RECOMENDAÇÃO HIERÁRQUICO COM PRIORIDADES ---
def buscar_musicas_hierarquicas(track, num_resultados=4):
    filtradas = []
    nomes_bloqueados = [track['title']] + [t['title'] for t in st.session_state.queue]
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio', 
        'extract_flat': False, 
        'skip_download': True,
        'ignoreerrors': True
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # --- PRIORIDADE 1: MESMO ÁLBUM ---
        try:
            query_album = f"{track['title']} album completo"
            info_album = ydl.extract_info(f"ytsearch3:{query_album}", download=False)
            if info_album and 'entries' in info_album:
                for entry in filter(None, info_album['entries']):
                    if entry.get('title') not in nomes_bloqueados and len(filtradas) < num_resultados:
                        if track.get('uploader', '').lower() in entry.get('uploader', '').lower():
                            d_str = entry.get('duration_string', '3:00')
                            filtradas.append({
                                'title': entry.get('title'), 'url': entry.get('webpage_url'), 'stream_url': entry.get('url'),
                                'uploader': entry.get('uploader'), 'duration': d_str, 'duration_secs': converter_duracao_segundos(d_str), 
                                'id': entry.get('id'), 'tag': '💿 MESMO ÁLBUM', 'tag_color': '#4A90E2'
                            })
                            nomes_bloqueados.append(entry.get('title'))
        except:
            pass

        # --- PRIORIDADE 2: MESMO ARTISTA (Fallback) ---
        if len(filtradas) < num_resultados:
            try:
                query_artista = f"{track.get('uploader', '')} top musicas"
                info_artista = ydl.extract_info(f"ytsearch4:{query_artista}", download=False)
                if info_artista and 'entries' in info_artista:
                    for entry in filter(None, info_artista['entries']):
                        if entry.get('title') not in nomes_bloqueados and len(filtradas) < num_resultados:
                            d_str = entry.get('duration_string', '3:00')
                            filtradas.append({
                                'title': entry.get('title'), 'url': entry.get('webpage_url'), 'stream_url': entry.get('url'),
                                'uploader': entry.get('uploader'), 'duration': d_str, 'duration_secs': converter_duracao_segundos(d_str), 
                                'id': entry.get('id'), 'tag': '👤 MESMO ARTISTA', 'tag_color': '#1DB954'
                            })
                            nomes_bloqueados.append(entry.get('title'))
            except:
                pass

        # --- PRIORIDADE 3: MESMA PLAYLIST / MIX (Último recurso) ---
        if len(filtradas) < num_resultados:
            try:
                query_mix = f"{track['title']} mix musicas semelhantes"
                info_mix = ydl.extract_info(f"ytsearch4:{query_mix}", download=False)
                if info_mix and 'entries' in info_mix:
                    for entry in filter(None, info_mix['entries']):
                        if entry.get('title') not in nomes_bloqueados and len(filtradas) < num_resultados:
                            d_str = entry.get('duration_string', '3:00')
                            filtradas.append({
                                'title': entry.get('title'), 'url': entry.get('webpage_url'), 'stream_url': entry.get('url'),
                                'uploader': entry.get('uploader'), 'duration': d_str, 'duration_secs': converter_duracao_segundos(d_str), 
                                'id': entry.get('id'), 'tag': '🎶 MIX / PLAYLIST', 'tag_color': '#7D3CFF'
                            })
                            nomes_bloqueados.append(entry.get('title'))
            except:
                pass
                
    return filtradas

def tocar_faixa(track):
    if st.session_state.current_track:
        st.session_state.history.append(st.session_state.current_track)
    st.session_state.current_track = track
    st.session_state.track_start_time = time.time()
    st.session_state.track_duration_secs = track.get('duration_secs', 180)

    with st.spinner("Analisando prioridades de reprodução por afinidade..."):
        novas_similares = buscar_musicas_hierarquicas(track)
    st.session_state.queue = novas_similares
    st.rerun()

def avancar_fila():
    if st.session_state.queue:
        proxima = st.session_state.queue.pop(0)
        tocar_faixa(proxima)
    else:
        st.session_state.current_track = None
        st.toast("Fim da rádio automática.", icon="🛑")
        st.rerun()

# --- REFRESH E MONITORAMENTO BACKEND (SERVER-SIDE GATILHO) ---
if st.session_state.current_track:
    st_autorefresh(interval=3000, key="track_timer")
    
    tempo_decorrido = time.time() - st.session_state.track_start_time
    tempo_restante = st.session_state.track_duration_secs - tempo_decorrido
    
    # Se faltar menos de 2 segundos no relógio do servidor, avança preemptivamente
    if tempo_restante <= 2:
        avancar_fila()

# --- INTERFACE ---
st.title("🎵 SpotPy: Infinite Radio Mode")
st.caption("Streaming contínuo estruturado por prioridade de Álbum, Artista e Playlist com transição híbrida.")
st.write("---")

search_query = st.text_input("", placeholder="Digite uma música ou artista para iniciar a rádio...", label_visibility="collapsed")

if search_query:
    if 'last_main_query' not in st.session_state or st.session_state.last_main_query != search_query:
        with st.spinner("Sintonizando frequências..."):
            ydl_opts_main = {
                'format': 'bestaudio[ext=m4a]/bestaudio', 
                'extract_flat': False, 
                'skip_download': True,
                'ignoreerrors': True
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts_main) as ydl:
                    info_main = ydl.extract_info(f"ytsearch10:{search_query}", download=False)
                
                if info_main and 'entries' in info_main and len(info_main['entries']) > 0:
                    results = []
                    for e in filter(None, info_main['entries']):
                        d_str = e.get('duration_string', '3:00')
                        results.append({
                            'title': e.get('title'), 'url': e.get('webpage_url'), 'stream_url': e.get('url'),
                            'uploader': e.get('uploader'), 'duration': d_str, 
                            'duration_secs': converter_duracao_segundos(d_str), 'id': e.get('id')
                        })
                    st.session_state.main_search_results = results
                    st.session_state.last_main_query = search_query
                else:
                    st.session_state.main_search_results = []
                    st.warning("Nenhum resultado válido encontrado para esta busca.")
            except Exception:
                st.error("Erro de conexão ao buscar no YouTube. Tente novamente.")
                st.session_state.main_search_results = []

    if 'main_search_results' in st.session_state and st.session_state.main_search_results:
        st.subheader("🎯 Escolha o ponto de partida:")
        
        for idx, track in enumerate(st.session_state.main_search_results):
            try:
                if not track or not track.get('title') or not track.get('id'):
                    continue
                with st.container(border=True):
                    col_info, col_btn = st.columns([8, 2])
                    with col_info:
                        st.markdown(f"**{idx+1}. {track['title'][:90]}...**" if len(track['title']) > 90 else f"**{idx+1}. {track['title']}**")
                        st.caption(f"{track.get('uploader', 'Desconhecido')} • {track.get('duration', '00:00')}")
                    with col_btn:
                        if st.button("Iniciar Rádio 📻", key=f"start_{track['id']}_{idx}", use_container_width=True):
                            tocar_faixa(track)
            except Exception:
                continue

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
        
        # Exibição do progresso aproximado calculado no backend
        elapsed = min(time.time() - st.session_state.track_start_time, st.session_state.track_duration_secs)
        pct = elapsed / st.session_state.track_duration_secs if st.session_state.track_duration_secs > 0 else 0.0
        st.progress(min(float(pct), 1.0), text=f"Progresso estimado: {int(elapsed)//60}:{int(elapsed)%60:02d} / {st.session_state.current_track['duration']}")
        
        # --- PLAYER HTML5 + JS (FADE OUT & TRANSMISSÃO FRONTEND) ---
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
                
                // Ativa o Fade-out faltando 4 segundos para acabar a mídia no navegador
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
                        // Envia comando para o Streamlit avançar a faixa via Component Value
                        window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'NEXT_TRACK'}}, '*');
                    }}
                }}, 200);
            }}
        </script>
        """
        
        response = components.html(js_player_component, height=90)
        
        # Se o gatilho Javascript responder com sucesso antes do backend, passa a música por aqui
        if response == 'NEXT_TRACK':
            avancar_fila()
        
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

    # COLUNA 2: A FILA DINÂMICA COM OS BADGES DE PRIORIDADE
    with col_queue_right:
        st.subheader("⏭️ A Seguir (Ordem de Afinidade)")
        
        if st.session_state.queue:
            for q_idx, q_track in enumerate(st.session_state.queue):
                with st.container(border=True):
                    col_q_info, col_q_play = st.columns([8, 2])
                    with col_q_info:
                        # Emite o badge colorido baseado no nível de prioridade mapeado
                        tag_label = q_track.get('tag', '🎶 RÁDIO SIMILAR')
                        tag_color = q_track.get('tag_color', '#7D3CFF')
                        st.markdown(f'<span class="priority-badge" style="background-color: {tag_color};">{tag_label}</span>', unsafe_allow_html=True)
                        
                        st.markdown(f"**{q_track['title'][:45]}...**" if len(q_track['title']) > 45 else f"**{q_track['title']}**")
                        st.caption(f"{q_track['uploader']} • {q_track['duration']}")
                    with col_q_play:
                        if st.button("▶️", key=f"play_q_{q_track['id']}_{q_idx}"):
                            st.session_state.queue.pop(q_idx)
                            tocar_faixa(q_track)
        else:
            st.write("Fila vazia.")
