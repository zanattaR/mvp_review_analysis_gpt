import pandas as pd
import numpy as np
import xlsxwriter
import base64
from io import BytesIO
import asyncio
import aiohttp
import json
import streamlit as st

# Função para transformar df em excel
def to_excel(df):
	output = BytesIO()
	writer = pd.ExcelWriter(output, engine='xlsxwriter')
	df.to_excel(writer, sheet_name='Planilha1',index=False)
	writer.close()
	processed_data = output.getvalue()
	return processed_data
	
# Função para gerar link de download
def get_table_download_link(df):
	val = to_excel(df)
	b64 = base64.b64encode(val)
	return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="extract.xlsx">Download</a>'

def replace_column_with_review(df_reviews, list_string):
    for column in df_reviews.columns:
        if column in list_string:
            df_reviews.rename(columns={column: "Review"}, inplace=True)
    return df_reviews

# Função para remover subcategorias genéricas
def check_col_subcategory(df_reviews):
    list_generic = ['Generic','Genérico','Reclamação Genérica','Elogio Genérico','Generic complaint','Generic compliment']
    
    if 'Subcategory' in df_reviews.columns:
        df_reviews = df_reviews[~df_reviews['Subcategory'].isin(list_generic)]
        df_reviews.reset_index(drop=True, inplace=True)
        return df_reviews
    else:
        return df_reviews

# Função para pegar uma amostra de reviews baseada na proporção de estrelas
def prop_rating(df_reviews):
    
    if 'Rating' in df_reviews.columns:        
        if df_reviews.shape[0] > 100:            
            df_reviews = train_test_split(df_reviews, train_size=100, stratify=df_reviews['Rating'])[0]
            df_reviews.reset_index(drop=True, inplace=True)
            return df_reviews
        else:
            return df_reviews
    else:
        return df_reviews

# Função que recebe o dataframe de reviews e adiciona a string 'Comentário: ', retornando uma lista dos reviews
def make_reviews(df_reviews):
    list_reviews = []
    for i in list(df_reviews['Review']):
        review = "Comentário: " + i
        list_reviews.append(review)
        
    return list_reviews

# Função que cria contexto para o modelo com as subcategorizações e detalhamentos
def create_system():
    
    system = """Based on a list of reviews made about an app written in portuguese,
    your role is to create an analysis pointing the main topics, the general sentiment in these comments.
    After that, create a plan of action based on the main topics and how to solve them """
    
    return system


async def get_data(session, body_mensagem):
    
    API_KEY = st.secrets["TOKEN_API"]

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    url = "/v1/chat/completions"
    
    response = await session.post(url, headers=headers, data=body_mensagem)
    body = await response.json()
    response.close()
    return body

# chatGPT - criação de respostas
async def get_chatgpt_responses(system, list_reviews):
    
    url_base = "https://api.openai.com"
    id_modelo = "gpt-3.5-turbo-16k"
    
    session = aiohttp.ClientSession(url_base)

    review_string = '\n'.join(list_reviews)

    body_mensagem = {

        "model": id_modelo,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": '''Here is the list of comments. Make the analysis in portuguese: ''' + review_string}
        ],
        "max_tokens":1800,
        "temperature": 1
    }

    body_mensagem = json.dumps(body_mensagem)
    data = await get_data(session,body_mensagem)

    await session.close()

    return data

# Normalização de resultados recebidos pela API
def normalize_results(results):
    df_results = pd.DataFrame(results['choices'])
    df_replies = pd.json_normalize(df_results['message'])['content'][0]

    return df_replies

def convert_string(str_results):
    
    converted_string = str_results.replace("\\n", "\n")
    
    return converted_string

# Tratamento de lotes de classificação
def clean_results(df_results):
    
    df_results['message.content'] = df_results['message.content'].str.replace("\n", ',')
    df_results['message.content'] = df_results['message.content'].apply(lambda x: eval('[' + x + ']'))
    df_results = df_results.explode('message.content').reset_index(drop=True)
    
    return df_results

# Acrescentar classificações no df de reviews, renomear colunas, adicionar valor Genérico caso não venha classificação da API
def format_results(df_reviews, df_results, group=''):
    
    df_reviews['results'] = df_results['message.content']
    df_reviews = pd.concat([df_reviews.drop('results', axis=1), df_reviews['results'].apply(pd.Series)], axis=1)
    df_reviews = df_reviews.rename(columns={0: group + "_pred"})
    
    df_reviews = df_reviews[['Review', group + "_pred"]]
    
    return df_reviews

# Substituir classificações que não estão na lista por nan
def replace_errors_with_nan(df_reviews, df_classes, group='', group_class=''):
    
    # Verificar valores da coluna "valor_b" com a coluna "lista_b"
    df_reviews[group] = np.where(df_reviews[group].isin(df_classes[group_class]), df_reviews[group], np.nan)

    return df_reviews












