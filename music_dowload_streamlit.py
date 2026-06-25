import os
import json
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

# --- CONFIGURAÇÃO ANTIBLOQUEIO (EMULA CLIENTE MÓVEL E YOUTUBE MUSIC) ---
CONFIG_ANTI_BLOCK = {
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'quiet': True,
    'no_warnings': True,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    },
    'extractor_args': {
        'youtube': {
            'player_client': ['ios', 'android'],  # Ignora restrições do cliente web tradicional
            'skip': ['dash', 'hls']
        }
    }
}

# --- INICIALIZAÇÃO DOS ESTADOS DE SESSÃO ---
if 'current_track' not in st.session_state:
    st.session_state.current_track = None
if 'queue' not in st.session_state:
    st.session_state.queue = []
if 'history' not in st.session_state:
    st.session_state.history = []

# --- MOTOR DE RECOMENDAÇÃO CONTÍNUA (YOUTUBE MUSIC ENGINE) ---
def buscar_musicas_similares(termo_referencia, num_resultados=4):
    try:
        query = f"{termo_referencia} mix"
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio', 
            'extract_flat': False, 
            'skip_download': True,
            **CONFIG_ANTI_BLOCK
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Busca no acervo específico de música
            info = ydl.extract_info(f"ytmusicsearch5:{query}", download=False)
            
        if info and 'entries' in info and len(info['entries']) > 0:
            filtradas = []
            nomes_bloqueados = [st.session_state.current_track['title']] if st.session_state.current_track else []
            nomes_bloqueados += [t['title'] for t in st.session_state.queue]
            
            for entry in info['entries']:
                if entry and isinstance(entry, dict) and entry.get('title') not in nomes_bloqueados:
                    url_stream = entry.get('url') or (entry.get('requested_formats')[0].get('url') if entry.get('requested_formats') else None)
                    if url_stream:
                        filtradas.append({
                            'title': entry.get('title'),
                            'url': entry.get('webpage_url') or '',
                            'stream_url': url_stream,
                            'uploader': entry.get('uploader') or entry.get('artists', ['Desconhecido'])[0],
                            'duration': entry.get('duration_string') or '3:30',
                            'id': entry.get('id') or f"sim_{len(filtradas)}",
                            'tag': '🎶 RÁDIO SIMILAR', 'tag_color': '#7D3CFF'
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
    
    with st.spinner("Gerando próximas faixas da rádio..."):
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
st.caption("Streaming contínuo via YouTube Music (Proteção contra Bloqueios ativa).")
st.write("---")

search_query = st.text_input("", placeholder="Digite uma música ou artista para iniciar a rádio...", label_visibility="collapsed")

if search_query:
    if 'last_main_query' not in st.session_state or st.session_state.last_main_query != search_query:
        with st.spinner("Buscando no ecossistema musical..."):
            ydl_opts_main = {
                'format': 'bestaudio[ext=m4a]/bestaudio', 
                'extract_flat': False, 
                'skip_download': True,
                **CONFIG_ANTI_BLOCK
            }
            with yt_dlp.YoutubeDL(ydl_opts_main) as ydl:
                try:
                    info_main = ydl.extract_info(f"ytmusicsearch3:{search_query}", download=False)
                except Exception as e:
                    st.error(f"Erro na extração de dados: {e}")
                    info_main = None

            if info_main and 'entries' in info_main and len(info_main['entries']) > 0:
                resultados_temporarios = []
                for idx, e in enumerate(info_main['entries']):
                    if e and isinstance(e, dict):
                        url_final_stream = e.get('url')
                        if not url_final_stream and e.get('requested_formats'):
                            url_final_stream = e['requested_formats'][0].get('url')

                        if url_final_stream:
                            resultados_temporarios.append({
                                'title': e.get('title'), 
                                'url': e.get('webpage_url') or '', 
                                'stream_url': url_final_stream,
                                'uploader': e.get('uploader') or e.get('artists', ['Desconhecido'])[0], 
                                'duration': e.get('duration_string') or '3:30', 
                                'id': e.get('id') or f"idx_{idx}"
                            })
                st.session_state.main_search_results = resultados_temporarios
                st.session_state.last_main_query = search_query

    if 'main_search_results' in st.session_state:
        if not st.session_state.main_search_results:
            st.warning("⚠️ O servidor recusou a requisição padrão. Modifique levemente o termo pesquisado.")
        else:
            st.subheader("🎯 Escolha o ponto de partida:")
            cols_start = st.columns(3)
            for idx, track in enumerate(st.session_state.main_search_results):
                if idx < len(cols_start):
                    with cols_start[idx]:
                        with st.container(border=True):
                            st.markdown(f"**{track['title'][:60]}...**" if len(track['title']) > 60 else f"**{track['title']}**")
                            st.caption(f"{track['uploader']} • {track['duration']}")
                            # Correção de Key duplicada injetando o idx numérico na string do botão
                            if st.button("Iniciar Rádio aqui 📻", key=f"start_btn_{idx}_{track['id']}", use_container_width=True):
                                tocar_faixa(track)

# --- PAINEL DO PLAYER DE ÁUDIO AVANÇADO ---
if st.session_state.current_track:
    st.write("---")
    col_player_left, col_queue_right = st.columns([6, 4])
    
    with col_player_left:
        st.markdown(f"""
            <div class="now-playing-box">
                <span style="color: #1DB954; font-size: 0.8rem; font-weight: bold; letter-spacing: 2px;">TOCANDO AGORA VIA STREAMING</span>
                <h2 style="margin-top: 5px; margin-bottom: 5px; font-size: 1.6rem;">{st.session_state.current_track['title']}</h2>
                <span style="color: #B3B3B3;">Artista: {st.session_state.current_track['uploader']} | Duração: {st.session_state.current_track['duration']}</span>
            </div>
        """, unsafe_allow_html=True)
        
        lista_streams = [st.session_state.current_track['stream_url']]
        lista_titulos = [st.session_state.current_track['title']]
        
        for t in st.session_state.queue:
            lista_streams.append(t['stream_url'])
            lista_titulos.append(t['title'])
            
        js_streams = json.dumps(lista_streams)
        js_titulos = json.dumps(lista_titulos)
        
        js_player_component = """
        <div style="background-color: #181818; padding: 15px; border-radius: 12px;">
            <audio id="audio-player" src="STREAM_INITIAL_URL" controls autoplay style="width: 100%; height: 40px;"></audio>
            <div id="player-status" style="color: #1DB954; font-size: 0.85rem; font-family: sans-serif; margin-top: 10px; text-align: center; font-weight: bold;">
                🔊 Tocando agora a faixa inicial
            </div>
        </div>

        <script>
            const playlistTracks = JS_STREAMS_ARRAY;
            const playlistTitles = JS_TITULOS_ARRAY;
            let currentIdx = 0;
            
            const audio = document.getElementById('audio-player');
            const statusDiv = document.getElementById('player-status');

            audio.addEventListener('ended', () => {
                currentIdx++;
                if (currentIdx < playlistTracks.length) {
                    statusDiv.innerText = "⏭️ Transicionando automaticamente...";
                    audio.src = playlistTracks[currentIdx];
                    audio.load();
                    audio.play()
                        .then(() => {
                            statusDiv.innerHTML = "🔊 Tocando sequência: <br><span style='color:#fff; font-weight:normal;'>" + playlistTitles[currentIdx] + "</span>";
                        })
                        .catch(err => {
                            statusDiv.innerText = "❌ Clique no Play para continuar a sequência";
                        });
                } else {
                    statusDiv.innerText = "🛑 Fim da sequência carregada.";
                }
            });
        </script>
        """.replace("STREAM_INITIAL_URL", lista_streams[0])\
           .replace("JS_STREAMS_ARRAY", js_streams)\
           .replace("JS_TITULOS_ARRAY", js_titulos)
        
        components.html(js_player_component, height=130)
        
        st.write("")
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.session_state.queue:
                texto_proxima = f"Avançar para: {st.session_state.queue[0]['title'][:25]}..."
            else:
                texto_proxima = "Fim da Fila"
                
            st.markdown('<div class="btn-secondary">', unsafe_allow_html=True)
            if st.button(f"⏭️ {texto_proxima}", use_container_width=True, disabled=not st.session_state.queue):
                avancar_fila()
            st.markdown('</div>', unsafe_allow_html=True)

        with c2:
            url_download = st.session_state.current_track['stream_url']
            nome_arquivo = f"{st.session_state.current_track['title']}.m4a".replace("/", "_")
            botao_download_html = f"""
                <a href="{url_download}" download="{nome_arquivo}" target="_blank" style="text-decoration: none;">
                    <button style="
                        width: 100%; background-color: #282828; color: #FFFFFF;
                        border: 1px solid #727272; border-radius: 50px; padding: 10px 24px;
                        font-weight: bold; cursor: pointer; font-family: sans-serif; font-size: 14px;
                    ">📥 Baixar Faixa (.m4a)</button>
                </a>
            """
            components.html(botao_download_html, height=50)

    # COLUNA 2: A FILA DINÂMICA
    with col_queue_right:
        st.subheader("⏭️ A Seguir (Fila Automática)")
        
        if st.session_state.queue:
            for q_idx, q_track in enumerate(st.session_state.queue):
                with st.container(border=True):
                    col_q_info, col_q_play = st.columns([8, 2])
                    with col_q_info:
                        st.markdown(f'<span class="priority-badge" style="background-color: {q_track["tag_color"]};">{q_track["tag"]}</span>', unsafe_allow_html=True)
                        st.markdown(f"**{q_idx+1}. {q_track['title'][:45]}...**" if len(q_track['title']) > 45 else f"**{q_track['title']}**")
                        st.caption(f"{q_track['uploader']} • {q_track['duration']}")
                    with col_q_play:
                        if st.button("▶️", key=f"play_q_{q_track['id']}_{q_idx}"):
                            st.session_state.queue.pop(q_idx)
                            tocar_faixa(q_track)
        else:
            st.write("Fila vazia.")
