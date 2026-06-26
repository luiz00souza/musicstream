import os
import streamlit as st
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
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO DOS ESTADOS DE SESSÃO ---
if 'current_track' not in st.session_state:
    st.session_state.current_track = None
if 'queue' not in st.session_state:
    st.session_state.queue = []
if 'history' not in st.session_state:
    st.session_state.history = []

# --- MOTOR DE RECOMENDAÇÃO CONTÍNUA ---
def buscar_musicas_similares(termo_referencia, num_resultados=4):
    try:
        query = f"{termo_referencia} mix musicas semelhantes"
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio', 
            'extract_flat': False, 
            'skip_download': True,
            'ignoreerrors': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch6:{query}", download=False)
            
        if info and 'entries' in info and len(info['entries']) > 0:
            filtradas = []
            nomes_bloqueados = [st.session_state.current_track['title']] if st.session_state.current_track else []
            nomes_bloqueados += [t['title'] for t in st.session_state.queue]
            
            for entry in filter(None, info['entries']):
                if entry.get('title') not in nomes_bloqueados:
                    filtradas.append({
                        'title': entry.get('title'),
                        'url': entry.get('webpage_url'),
                        'stream_url': entry.get('url'),
                        'uploader': entry.get('uploader'),
                        'duration': entry.get('duration_string'),
                        'id': entry.get('id')
                    })
                if len(filtradas) >= num_resultados:
                    break
            return filtradas
    except:
        return []
    return []

def tocar_faixa(track):
    if st.session_state.current_track:
        st.session_state.history.append(st.session_state.current_track)
    st.session_state.current_track = track
    
    novas_similares = buscar_musicas_similares(track['title'])
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
st.caption("Streaming contínuo com Autoplay e Crossfade nativo no navegador.")
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
                    st.session_state.main_search_results = [{
                        'title': e.get('title'), 'url': e.get('webpage_url'), 'stream_url': e.get('url'),
                        'uploader': e.get('uploader'), 'duration': e.get('duration_string'), 'id': e.get('id')
                    } for e in filter(None, info_main['entries'])]
                    st.session_state.last_main_query = search_query
                else:
                    st.session_state.main_search_results = []
                    st.warning("Nenhum resultado válido encontrado para esta busca.")
            except Exception:
                st.error("Erro de conexão ao buscar no YouTube. Tente novamente em alguns segundos.")
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
        
        src_audio = st.session_state.current_track['stream_url']
        
        # Player persistente injetado via st.markdown para evitar os problemas de reset do iframe
        js_player_component = f"""
        <div id="player-container"></div>
        <script>
        (function() {{
            var globalPlayer = window.parent.document.getElementById('global-audio-player');
            var container = document.getElementById('player-container');
            var targetSrc = "{src_audio}";

            if (!globalPlayer) {{
                // Criar o elemento do player pela primeira vez na janela global
                var playerWrapper = document.createElement('div');
                playerWrapper.style.backgroundColor = '#181818';
                playerWrapper.style.padding = '15px';
                playerWrapper.style.borderRadius = '30px';
                playerWrapper.style.display = 'flex';
                playerWrapper.style.alignItems = 'center';
                playerWrapper.style.justifyContent = 'center';
                playerWrapper.innerHTML = '<audio id="global-audio-player" src="' + targetSrc + '" controls autoplay style="width: 100%; border-radius: 30px; height: 40px;"></audio>';
                
                container.appendChild(playerWrapper);
                globalPlayer = window.parent.document.getElementById('global-audio-player');
                setupAudioEvents(globalPlayer);
            }} else {{
                // Mover o player existente para o container atual para manter o layout visual correto
                container.appendChild(globalPlayer.parentElement);
                
                // Se a música mudou na sessão, atualiza o arquivo de áudio
                if (globalPlayer.getAttribute('src') !== targetSrc) {{
                    globalPlayer.src = targetSrc;
                    globalPlayer.volume = 1.0;
                    globalPlayer.play();
                }}
            }}

            function setupAudioEvents(audio) {{
                var fadeTriggered = false;

                audio.addEventListener('timeupdate', function() {{
                    var timeLeft = audio.duration - audio.currentTime;
                    
                    // Dispara o crossfade nos últimos 4 segundos
                    if (timeLeft <= 4 && !fadeTriggered && audio.duration > 0) {{
                        fadeTriggered = true;
                        fadeVolumeOut(audio);
                    }}
                }});

                audio.addEventListener('play', function() {{
                    fadeTriggered = false;
                }});

                function fadeVolumeOut(player) {{
                    var volume = player.volume;
                    var interval = setInterval(function() {{
                        if (volume > 0.05) {{
                            volume -= 0.05;
                            player.volume = volume;
                        }} else {{
                            player.volume = 0;
                            clearInterval(interval);
                            
                            // Procura o botão "Avançar" do Streamlit e simula o clique do usuário
                            var buttons = window.parent.document.querySelectorAll('button');
                            for (var i = 0; i < buttons.length; i++) {{
                                if (buttons[i].innerText.includes('⏭️')) {{
                                    buttons[i].click();
                                    break;
                                }}
                            }}
                        }}
                    }}, 200);
                }}
            }}
        }})();
        </script>
        """
        
        st.markdown(js_player_component, unsafe_allow_html=True)
        
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

    # COLUNA 2: A FILA DINÂMICA
    with col_queue_right:
        st.subheader("⏭️ A Seguir (Fila Automática)")
        
        if st.session_state.queue:
            for q_idx, q_track in enumerate(st.session_state.queue):
                with st.container(border=True):
                    col_q_info, col_q_play = st.columns([8, 2])
                    with col_q_info:
                        st.markdown(f"**{q_idx+1}. {q_track['title'][:45]}...**" if len(q_track['title']) > 45 else f"**{q_track['title']}**")
                        st.caption(f"{q_track['uploader']} • {q_track['duration']}")
                    with col_q_play:
                        if st.button("▶️", key=f"play_q_{q_track['id']}_{q_idx}"):
                            st.session_state.queue.pop(q_idx)
                            tocar_faixa(q_track)
        else:
            st.write("Fila vazia.")
