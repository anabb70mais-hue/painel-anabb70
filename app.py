import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import base64

# 1. Configuração da página (Deve ser a primeira linha)
st.set_page_config(page_title="Monitor de Associados ANABB 70+", layout="wide")

# 2. Função para colocar a imagem de fundo e arrumar o logo do topo
def add_bg_from_local(image_file):
    with open(image_file, "rb") as file:
        encoded_string = base64.b64encode(file.read()).decode()
    st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url(data:image/jpeg;base64,{encoded_string});
        background-size: cover;
        background-position: top; /* <--- ISSO GARANTE QUE O TOPO NUNCA SEJA CORTADO */
        background-attachment: fixed;
    }}
    /* Deixar o fundo das tabelas levemente transparente/branco para leitura */
    .stDataFrame {{
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 10px;
        padding: 10px;
    }}
    /* Ajusta o espaço do conteúdo para não ficar em cima da faixa preta do logo */
    .block-container {{
        padding-top: 5.5rem; 
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
    # Malha geográfica do Brasil para desenhar o mapa
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    response = requests.get(url)
    return json.loads(response.text)

df = load_data()
brazil_states = load_geojson()

# 4. Preparando Dados Gerais
total_base = len(df)
df_uf = df.groupby('UF').size().reset_index(name='Quantidade')
df_uf['Porcentagem'] = (df_uf['Quantidade'] / total_base) * 100

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
    
    # Ajustando o mapa
    fig.update_geos(fitbounds="locations", visible=False, bgcolor='rgba(0,0,0,0)')
    fig.update_layout(
        height=650, 
        margin={"r":0,"t":0,"l":0,"b":0},
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        coloraxis_showscale=False 
    )
    
    # Formatando o balão do mouse (Hover)
    fig.update_traces(hovertemplate="<b>Estado: %{location}</b><br>Associados: %{customdata[0]}<br>Base: %{customdata[1]:.2f}%<extra></extra>")
    
    # Mostra o mapa e captura o clique
    event = st.plotly_chart(fig, use_container_width=True, on_select="rerun")

with col2:
    # 6. Lógica da Tabela Lateral (Detalhamento)
    if len(event.selection.points) > 0:
        # Se clicou em um estado
        estado_selecionado = event.selection.points[0]['location']
        
        st.subheader(f"Detalhamento: {estado_selecionado}")
        
        # Filtra e agrupa por cidade
        df_cidades = df[df['UF'] == estado_selecionado].groupby('Cidade').size().reset_index(name='Qtd')
        df_cidades = df_cidades.sort_values(by='Qtd', ascending=False).reset_index(drop=True)
        
        # Calcula porcentagem dentro do estado
        total_estado = df_cidades['Qtd'].sum()
        df_cidades['% no Estado'] = (df_cidades['Qtd'] / total_estado * 100).round(2).astype(str) + '%'
        
        st.dataframe(df_cidades, use_container_width=True, hide_index=True)
        
        # Rodapé de totais
        st.write("---")
        st.markdown(f"**Total no Estado ({estado_selecionado}):** {total_estado}")
        st.markdown(f"**Total no Brasil:** {total_base}")
    else:
        # Mensagem padrão antes de clicar
        st.info("👈 Clique em um estado no mapa para ver a lista de cidades aqui.")
        
        st.write("**Top 5 Estados Gerais:**")
        st.dataframe(df_uf[['UF', 'Quantidade']].sort_values('Quantidade', ascending=False).head(5), hide_index=True)
