import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup as bs
from requests import get
import streamlit.components.v1 as components

# theme to apply to graphics
sns.set_theme()
sns.set_style('darkgrid')

# App name
st.markdown("<h1 style='text-align: center; color: black;'>Yves KATE Scrappper APP</h1>", unsafe_allow_html=True)

# Description
st.markdown("""
<p style="color: black">This application scrapes data from multiple web pages and also provides access to previously scraped data, 
allowing users to download it directly without the need for additional scraping.<br>
<em>Python libraries:</em> base64, pandas, streamlit, requests, bs4<br>
<em>Data source:</em> <a href='https://sn.coinafrique.com/categorie/poules-lapins-et-pigeons'>[poules-lapins-et-pigeons]</a> -- <a href='https://sn.coinafrique.com/categorie/autres-animaux'>[autres-animaux]</a>.
</p>""", unsafe_allow_html=True)


# this function turns a pd.DataFrame into a csv file
def convert_df(df):
    return df.to_csv().encode('utf-8')


# this function loads a dataset in order to make it downloadable
def load(dataframe, title, key, key1) :
    st.markdown("""
    <style>
    div.stButton {text-align:center}
    </style>""", unsafe_allow_html=True)

    if st.button(title,key1):
        # st.header(title)

        st.subheader('Display data dimension')
        st.write('Data dimension: ' + str(dataframe.shape[0]) + ' rows and ' + str(dataframe.shape[1]) + ' columns.')
        st.dataframe(dataframe)

        csv = convert_df(dataframe)

        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name='Data.csv',
            mime='text/csv',
            key = key)


# Function to load a local CSS stylesheet to improve the appearance of the application
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


# Function to retrieve data from pages containing advertisements for chickens, rabbits and pigeons
@st.cache_data  # Data caching to avoid redoing scraping at each execution
def load_poules_lapins_pigeons_data(num_of_page):
    # create a empty dataframe df
    df = pd.DataFrame()
    # loop over pages indexes
    for p_index in range(1, int(num_of_page)+1):
        url = f'https://sn.coinafrique.com/categorie/poules-lapins-et-pigeons?&page={p_index}'
        # get the html code of the page using the get function requests
        res = get(url)
        # store the html code in a beautifulsoup objet with a html parser (a parser allows to easily navigate through the html code)
        soup = bs(res.text , 'html.parser')
        # get all containers that contains the informations of each car
        containers = soup.find_all('div', class_ = 'col s6 m4 l3')
        # scrape data from all the containers
        data = []
        for container in containers: 
            try:
                detail = container.find('p', class_='ad__card-description').find('a').text.strip()
                prix = container.find('p', class_='ad__card-price').find('a').text.strip('CFA').replace(' ', '') if "Prix sur demande" not in container.find('p', class_='ad__card-price').find('a').text else "Prix sur demande"
                adresse = container.find('p', class_='ad__card-location').find('span').text
                img_link = container.find('img', class_='ad__card-img')['src']
                dic = {'detail': detail, 'prix': prix, 'adresse': adresse, 'img_link': img_link}
                data.append(dic)
            except Exception as e:
                print(f"Erreur lors du scraping: {e}")
            finally:
                pass
        
        DF = pd.DataFrame(data)
        df= pd.concat([df, DF], axis =0).reset_index(drop = True) 
    return df   

# Function to retrieve data from other animals on multiple pages
@st.cache_data  # Data caching to avoid redoing scraping at each execution
def load_autres_animaux_data(num_of_page):
    # create a empty dataframe df
    df=pd.DataFrame()
    # loop over pages indexes
    for p_index in range (1, int(num_of_page) + 1):
        url=f'https://sn.coinafrique.com/categorie/autres-animaux?&page={p_index}'
        #get the html code of the page using the get function reauests
        res=get(url)
        # store the html code in a beautifulsoup object zith a html panser
        soup=bs(res.text,'html.parser')
        # get all containers that contains the informations of each car
        containers = soup.find_all('div', class_ = 'col s6 m4 l3')
        data=[]
        for container in containers:
            try:

                nom = container.find('p', class_='ad__card-description').find('a').text.strip()
                prix = container.find('p', class_='ad__card-price').find('a').text.strip('CFA').replace(' ',
                                                                                                        '') if "Prix sur demande" not in container.find(
                    'p', class_='ad__card-price').find('a').text else container.find('p', class_='ad__card-price').find(
                    'a').text
                adresse = container.find('p', class_='ad__card-location').find('span').text
                img_link = container.find('img', class_='ad__card-img')['src']
                dic = {'nom': nom, 'prix': prix, 'adresse': adresse, 'img_link': img_link}
                data.append(dic)
            except Exception as e:
                print(f"Erreur lors du scraping: {e}")
            finally:
                pass
        DF=pd.DataFrame(data)
        df=pd.concat([df,DF], axis=0 ).reset_index(drop=True)

    return df

# this function extracts the city name from the 'address' column of the df
def extract_city(address):
    parts = address.split(',')
    if len(parts) >= 2:
        return parts[-2].strip()  # The penultimate element is the city
    else:
        return "Non renseigné"

# this function generates a dataframe suitable for a barplot type graph
def generate_df_counts(df):
    df['prix_clean'] = pd.to_numeric(df['prix'], errors='coerce')
    df['Ville'] = df.adresse.apply(extract_city)
    bins = range(0, int(df["prix_clean"].max()) + 60000, 60000)
    labels = [f"{b}-{b + 60000}" for b in bins[:-1]]
    df["class_prix"] = pd.cut(df["prix_clean"], bins=bins, labels=labels, include_lowest=True)

    df_counts = df["Ville"].value_counts().sort_values(ascending=False).reset_index()
    df_counts.columns = ["Ville", "Nombre"]

    return df_counts

# this function generates a dataframe suitable for a boxplot type graph
def generate_df_filtered(df):
    df['prix_clean'] = pd.to_numeric(df['prix'], errors='coerce')
    df['Ville'] = df.adresse.apply(extract_city)
    df_filtered = df.dropna(subset=["prix_clean", "Ville"])

    return df_filtered


# User interface with Streamlit
st.sidebar.header('User Panel')

# Selection of the number of pages to scrape
Pages = st.sidebar.selectbox('Pages indexes', list([int(p) for p in np.arange(2, 600)]))

# Selection of the action to be executed
Choices = st.sidebar.selectbox('Options', ['Scrape data using beautifulSoup', 'Download scraped data',  'Fill the form with Kobo ToolBox', 'Fill the form with Google Forms'])

# loading the css file into the page
local_css('style.css')  

if Choices=='Scrape data using beautifulSoup':

    # Loading and displaying data
    poules_lapins_pigeons_data_mul_pag = load_poules_lapins_pigeons_data(Pages)
    autres_animaux_data_mul_pag = load_autres_animaux_data(Pages)

    load(poules_lapins_pigeons_data_mul_pag, 'poules_lapins_pigeons data', '1', '101')
    load(autres_animaux_data_mul_pag, 'autres_animaux data', '2', '102')

    st.markdown("<h2 style='text-align: center; color: black'>Visualizations</h2>", unsafe_allow_html=True)

    st.markdown("<h3 style='text-align: center; color: black'>Poules, Lapins, Pigeons</h3>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with st.container():
        c1.markdown("<p style='font-size: 13px; color: black'>Nombre d'articles par ville</p>", unsafe_allow_html=True)
        c2.markdown("<p style='font-size: 13px; color: black'>Distribution des prix par ville</p>", unsafe_allow_html=True)

    with c1:
        fig, ax = plt.subplots(figsize=(6, 4))
        chart_data = generate_df_counts(poules_lapins_pigeons_data_mul_pag)

        sns.barplot(x='Ville', y='Nombre', data=chart_data, ax=ax)

        ax.set_xlabel("Ville")
        ax.set_ylabel("Nombre")


        plt.xticks(rotation=60)

        st.pyplot(fig)

    with c2:
        chart_data = generate_df_filtered(poules_lapins_pigeons_data_mul_pag)
        fig, axs = plt.subplots(figsize=(6, 4))

        sns.boxplot(x = 'Ville', y = 'prix_clean', data=chart_data, orient='v', ax=axs)

        ax.set_xlabel("Ville")
        ax.set_ylabel("Prix total")



        plt.xticks(rotation=60)

        st.pyplot(fig)


    st.markdown("<h3 style='text-align: center; color: black'>Autres animaux</h3>", unsafe_allow_html=True)
    c3, c4 = st.columns(2)

    with st.container():
        c3.markdown("<p style='font-size: 13px; color: black'>Nombre d'articles par ville</p>", unsafe_allow_html=True)
        c4.markdown("<p style='font-size: 13px; color: black'>Distribution des prix par ville</p>", unsafe_allow_html=True)

    with c3:
        chart_data = generate_df_counts(autres_animaux_data_mul_pag)
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.barplot(x='Ville', y='Nombre', data=chart_data, ax=ax)

        ax.set_xlabel("Ville")
        ax.set_ylabel("Nombre")


        plt.xticks(rotation=60)

        st.pyplot(fig)

    with c4:
        chart_data = generate_df_filtered(autres_animaux_data_mul_pag)
        fig, axs = plt.subplots(figsize=(6, 4))
        sns.boxplot(x='Ville', y='prix_clean', data=chart_data, orient='v', ax=axs)

        ax.set_xlabel("Ville")
        ax.set_ylabel("Prix total")


        plt.xticks(rotation=60)

        st.pyplot(fig)


elif Choices == 'Download scraped data':
    poules_lapins_pigeons = pd.read_csv('poules-lapins-et-pigeons-web-scraper.csv')
    autres_animaux = pd.read_csv('autres-animaux-web-scraper.csv')

    load(poules_lapins_pigeons, 'poules_lapins_pigeons data', '1', '101')
    load(autres_animaux, 'autres_animaux data', '2', '102')

elif Choices == 'Fill the form with Kobo ToolBox':
    components.html("""<iframe src=https://ee.kobotoolbox.org/i/xGrhVpgS width="800" height="600"></iframe>""",height=1100,width=800)

else:
    components.html("""<iframe src="https://docs.google.com/forms/d/e/1FAIpQLScxLwuJLF4hDuDbBGJyE8mL5wlyBLMayhY-_VInWUTADnr_BQ/viewform?embedded=true" width="640" height="752" frameborder="0" marginheight="0" marginwidth="0">Chargement…</iframe>""",height=1100,width=800)