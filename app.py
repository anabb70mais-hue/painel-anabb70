import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import base64

# 1. Configuração da página (Deve ser a primeira linha)
st.set_page_config(page_title="Monitor de Associados ANABB 70+", layout="wide")

# 2. Função para colocar a imagem de fundo e ajustar os espaços
def add_bg_from_local(image_file):
    with open(image_file, "rb") as file:
        encoded_string = base64.b64encode(file.read()).decode()
    st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url(data:image/jpeg;base64,{encoded_string});
        background-size: cover;
        background-position: top; 
        background-attachment: fixed;
    }}
    /* Fundo das tabelas */
    .stDataFrame {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 10px;
        padding: 10px;
    }}
    /* Ajusta o espaço do conteúdo para não ficar em cima do logo */
    .block-container {{
        padding-top: 5.5rem; 
    }}
    /* Estilo para as novas caixas de resumo (WhatsApp e Evolução) */
    .metric-card {{
        background-color: rgba(240, 242, 246, 0.95);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-top: 15px;
    }}
    </style>
    """,
    unsafe_allow_html=True
    )

# Aplica o fundo
try:
    add_bg_from_local('Fundo.jpg')
except Exception as e:
    pass

# 3. Carregando os Dados
@st.cache_data
def load_data():
    df = pd.read_excel('Relatorio 70+Completo 14.08.xlsx', usecols=['UF', 'Cidade', 'Matrícula'])
    return df

@st.cache_data
def load_geojson():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    response = requests.get(url)
    return json.loads(response.text)

df = load_data()
brazil_states = load_geojson()

# 4. Preparando Dados Gerais
total_base = len(df)
df_uf = df.groupby('UF').size().reset_index(name='Quantidade')
df_uf['Porcentagem'] = (df_uf['Quantidade'] / total_base) * 100

# Base de Dados Consolidada do WhatsApp (Extraída da imagem anterior)
whatsapp_data = {
    'DF': 198, 'MG': 164, 'CE': 133, 'PB': 120, 'BA': 114, 'RS': 108,
    'PR': 99, 'SP': 95, 'RN': 91, 'PE': 90, 'RJ': 80, 'GO': 79,
    'MA': 75, 'PA': 49, 'MS': 43, 'ES': 39, 'PI': 38, 'AL': 33,
    'AM': 32, 'MT': 31, 'SC': 19, 'TO': 19, 'SE': 15
}

st.title("Monitor de Associados por Estado")

# 5. Dividindo a tela
col1, col2 = st.columns([6, 4])

with col1:
    # Criando o Mapa Coroplético do Brasil
    fig = px.choropleth(
        df_uf,
        geojson=brazil_states,
        locations='UF',
        featureidkey="properties.sigla",
        color='Porcentagem',
        color_continuous_scale="Blues", 
        custom_data=['Quantidade', 'Porcentagem'] 
    )
    
    # Ajustando o mapa (altura reduzida levemente para caber os quadros novos)
    fig.update_geos(fitbounds="locations", visible=False, bgcolor='rgba(0,0,0,0)')
    fig.update_layout(
        height=550, 
        margin={"r":0,"t":0,"l":0,"b":0},
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        coloraxis_showscale=False 
    )
    
    fig.update_traces(hovertemplate="<b>Estado: %{location}</b><br>Associados: %{customdata[0]}<br>Base: %{customdata[1]:.2f}%<extra></extra>")
    
    # Mostra o mapa e captura o clique
    event = st.plotly_chart(fig, use_container_width=True, on_select="rerun")
    
    # NOVAS INSERÇÕES: Caixas de resumo lado a lado sob o mapa
    subcol1, subcol2 = st.columns(2)
    
    with subcol1:
        if len(event.selection.points) > 0:
            estado_selecionado = event.selection.points[0]['location']
            total_estado = df_uf[df_uf['UF'] == estado_selecionado]['Quantidade'].values[0]
            whats_membros = whatsapp_data.get(estado_selecionado, 0)
            
            # Evita erro de divisão por zero caso algum estado esteja vazio
            percentual = (whats_membros / total_estado * 100) if total_estado > 0 else 0
            
            st.markdown(f"""
            <div class="metric-card">
                <h4 style="margin:0 0 10px 0; color:#1f3b73;">{estado_selecionado}</h4>
                <table style="width:100%; text-align:left; font-size:14px; border-collapse: collapse;">
                    <tr style="background-color: #e6e9ef;"><td style="padding: 5px;"><b>Sócio 70+</b></td><td style="text-align:right; padding: 5px;">{total_estado}</td></tr>
                    <tr><td style="padding: 5px;"><b>Whatsapp</b></td><td style="text-align:right; padding: 5px;">{whats_membros}</td></tr>
                    <tr style="background-color: #e6e9ef;"><td style="padding: 5px;"><b>Percentual</b></td><td style="text-align:right; padding: 5px;">{percentual:.2f}%</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="metric-card" style="opacity: 0.6; padding-top: 40px; padding-bottom: 40px;">
                <p style="margin:0; color:#1f3b73;">👆 Clique em um estado no mapa para ver o resumo do WhatsApp.</p>
            </div>
            """, unsafe_allow_html=True)
            
    with subcol2:
        st.markdown("""
        <div class="metric-card" style="padding-top: 25px; padding-bottom: 25px;">
            <p style="margin:0; color:#1f3b73; font-weight:bold; font-size:16px;">Evolução de Associados</p>
            <div style="font-size: 28px; font-weight: bold; color: #4CAF50;">↗ 40.000 <span style="font-size:14px; color:#666;">(2026)</span></div>
            <div style="font-size: 16px; color: #888; margin-top:5px;">35.000 <span style="font-size:12px;">(2025)</span></div>
        </div>
        """, unsafe_allow_html=True)

with col2:
    if len(event.selection.points) > 0:
        estado_selecionado = event.selection.points[0]['location']
        
        st.subheader(f"Detalhamento: {estado_selecionado}")
        
        df_cidades = df[df['UF'] == estado_selecionado].groupby('Cidade').size().reset_index(name='Qtd')
        df_cidades = df_cidades.sort_values(by='Qtd', ascending=False).reset_index(drop=True)
        
        total_estado = df_cidades['Qtd'].sum()
        df_cidades['% no Estado'] = (df_cidades['Qtd'] / total_estado * 100).round(2).astype(str) + '%'
        
        st.dataframe(df_cidades, use_container_width=True, hide_index=True)
        
        # OS TOTAIS DO RODAPÉ FORAM REMOVIDOS AQUI CONFORME SOLICITADO
        
    else:
        st.info("👈 Clique em um estado no mapa para ver a lista de cidades aqui.")
        st.write("**Top 5 Estados Gerais:**")
        st.dataframe(df_uf[['UF', 'Quantidade']].sort_values('Quantidade', ascending=False).head(5), hide_index=True)
