#### MVP - CLASSIFICATION GPT
import streamlit as st
import pandas as pd
import numpy as np
import xlsxwriter
import json
import base64
from io import BytesIO
import asyncio
import aiohttp
from utils import *
import time
import sklearn
from sklearn.model_selection import train_test_split

st.title("Review Analysis GPT")
st.write('Esta aplicação tem como objetivo auxiliar na análise de reviews com o uso de IA')
st.write()

# Inserindo arquivo de reviews
reviewSheet = st.file_uploader("Insira um arquivo .xlsx com os reviews a serem classificados (Máx: 100 reviews)")
if reviewSheet is not None:
    df_reviews = pd.read_excel(reviewSheet)

    # Lendo reviews e verificando se há mais de 100 registros
    if df_reviews.shape[0] > 100:
        st.warning("Há mais de 100 reviews nesta base, a classificação só será feita com os 100 primeiros.")

    # Filtrando os 100 primeiros reviews
    #df_reviews = df_reviews.iloc[:100]


# Visualizar dados
check_reviews = st.checkbox("Visualizar Reviews")
if reviewSheet is not None:
    if check_reviews:
        st.write(df_reviews)


############# Tratamento e preparação de dados #############
if reviewSheet is not None:

    # Substituindo variações de nomes de reviews
    list_string = ['Text','text','TEXT','Reviews','reviews','REVIEW','REVIEWS']
    df_reviews = replace_column_with_review(df_reviews, list_string)

    # Remover comentários genéricos
    df_reviews = check_col_subcategory(df_reviews)

    # Segmentar proporção de reviews por ratings
    df_reviews = prop_rating(df_reviews)

    # Criar lista de reviews com a string 'Comentário: ' no início
    list_reviews = make_reviews(df_reviews)

    # Particionar lotes de reviews para serem enviados em conjunto na API
    #lotes_reviews = coletar_lotes(list_reviews,1)

    # Criação de contexto para o modelo. A função recebe as classes para compor o texto
    system  = create_system()

############# Tratamento e preparação de dados #############
if st.button('Gerar Classificações'):

    # Request na API p/ gerar classificações
    results = asyncio.run(get_chatgpt_responses(system, list_reviews))

    # Normalização de resultados recebidos pela API
    str_results = normalize_results(results)

    st.write(convert_string(str_results))

    # # Tratamento de lotes de classificação
    # df_results_sentiment = clean_results(df_results_sentiment)
    # df_results_category = clean_results(df_results_category)
    # df_results_subcategory = clean_results(df_results_subcategory)
    # df_results_detail = clean_results(df_results_detail)

    # # Acrescentar classificações no df de reviews, renomear colunas, adicionar valor Genérico caso não venha classificação da API
    # df_reviews_sentiment = format_results(df_reviews=df_reviews, df_results=df_results_sentiment, group="Sentiment")
    # df_reviews_category = format_results(df_reviews=df_reviews, df_results=df_results_category, group="Category")
    # df_reviews_subcategory = format_results(df_reviews=df_reviews, df_results=df_results_subcategory, group="Subcategory")
    # df_reviews_detail = format_results(df_reviews=df_reviews, df_results=df_results_detail, group="Detailing")

    # # Substituir classificações que não estão na lista por nan
    # df_reviews_subcategory = replace_errors_with_nan(df_reviews=df_reviews_subcategory, df_classes=df_classes, group='Subcategory_pred', group_class='Subcategoria')
    # df_reviews_detail = replace_errors_with_nan(df_reviews=df_reviews_detail, df_classes=df_classes, group='Detailing_pred', group_class='Detalhamento')

    # # Concatenar dfs de grupos
    # df_final = pd.concat([df_reviews_sentiment, df_reviews_category, df_reviews_subcategory, df_reviews_detail], axis=1)
    # df_final = df_final.loc[:, ~df_final.columns.duplicated()]

    # st.write(df_final)
    # st.write('Clique em Download para baixar o arquivo')
    # st.markdown(get_table_download_link(df_final), unsafe_allow_html=True)


