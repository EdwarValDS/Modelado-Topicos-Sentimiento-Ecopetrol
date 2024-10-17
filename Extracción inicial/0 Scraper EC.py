from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
from dateutil import parser

from bs4 import BeautifulSoup
from urllib.request import urlopen, Request
from urllib.error import HTTPError
import pandas as pd
from datetime import datetime
import re
from deep_translator import GoogleTranslator

def scraper_ec():

    meses_mapping = {
        'ene': 'Jan',
        'feb': 'Feb',
        'mar': 'Mar',
        'abr': 'Apr',
        'may': 'May',
        'jun': 'Jun',
        'jul': 'Jul',
        'ago': 'Aug',
        'sep': 'Sep',
        'oct': 'Oct',
        'nov': 'Nov',
        'dic': 'Dec'
    }

    options = Options()
    options.add_experimental_option("detach",True)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://www.larepublica.co/buscar?term=ecopetrol")
    #driver.maximize_window()

    time.sleep(10)

    max_duration_seconds = 15
    start_time = time.time()

    try:
        while time.time() - start_time < max_duration_seconds:
            ver_mas_button = driver.find_element(By.CLASS_NAME, "btn.analisisSect")
            ver_mas_button.location_once_scrolled_into_view
            time.sleep(2)
            ver_mas_button.click()
    except Exception as e:
        print(f"No se pudo hacer clic en el botón 'VER MÁS': {e}")
    finally:
        html = driver.page_source
        #with open("html_ec_republica.txt", "w", encoding="utf-8") as file:
        #    file.write(html)
    driver.quit()

    html = BeautifulSoup(html, "html.parser")

    articles = html.find("div", class_="result-list")


    articles = articles.find_all('a', class_='result')

    titles = []
    links = []
    dates = []

    for link in articles:
        title = link.find('h3').text
        url = link['href']
        date = link.find('span', class_='date').text

        titles.append(title)
        links.append(url)
        dates.append(date)

    data1 = pd.DataFrame({"Date": dates, "Title": titles, "Link": links})

    data1["Link"] = "https://www.larepublica.co" + data1["Link"] 

    texts = []
    leads = []

    for l in data1["Link"]:
        req = Request(url=l)
        try: 
            response = urlopen(req)
            html = BeautifulSoup(response, "html.parser")
            try:
                lead = html.find("div", class_="lead").text
                new = html.find("div", class_="html-content").text
                lead = lead.replace('\n', ' ')
                new = new.replace('\n', ' ')
                text = lead + new
                texts.append(text)
                leads.append(lead)
            except:
                lead = "na"
                new  = "na"
                text = lead + new
                texts.append(text)
                leads.append(lead)
        except HTTPError as e:
            if e.code == 404:
                continue
            else:
                continue
        time.sleep(1)

    data1["Headline"] = leads
    data1["Article"] = texts


    # Limpieza inicial
    data1['Article'] = data1['Article'].str.replace(r'\[[^\]]*\]', '') 
    data1['Article'] = data1['Article'].str.replace(r'\n', ' ')  
    data1['Article'] = data1['Article'].str.strip()  
    data1['Title'] = data1['Title'].str.replace(r'\[[^\]]*\]', '') 
    data1['Title'] = data1['Title'].str.replace(r'\n', ' ')  
    data1['Title'] = data1['Title'].str.strip()  
    data1['Headline'] = data1['Headline'].str.replace(r'\[[^\]]*\]', '') 
    data1['Headline'] = data1['Headline'].str.replace(r'\n', ' ')  
    data1['Headline'] = data1['Headline'].str.strip()  


    data1["Source"] = "La República"

    data1['Date'] = data1['Date'].str.replace('.', '')

    data1['Date'] = data1['Date'].apply(lambda x: ' '.join([meses_mapping[mes] if mes in meses_mapping else mes for mes in x.split()]))
    data1['Date'] = pd.to_datetime(data1['Date'], format='%b %d, %Y', errors='coerce')

    columns_to_translate = ["Title","Headline"]

    for column in columns_to_translate:
        try:
          data1[column] = data1[column].apply(lambda x: GoogleTranslator(source='es', target='en').translate(x))
        except:
          pass

    #data1.to_csv("./LaRepublica.csv", index=False)

    old_data1 = pd.read_csv("./Datos/Datos_analisis_EC_traducidos.csv")
    old_data1 = old_data1[["Date","Title","Link","Headline","Article","Source"]]
    new_data1 = pd.concat([old_data1,data1], ignore_index=True).drop_duplicates(subset=["Link"])
    new_data1 = new_data1[["Date","Title","Link","Headline","Article","Source"]]
    #new_data1["Date"] = pd.to_datetime(new_data1["Date"])
    #new_data1 = new_data1.sort_values(by="Date")
    new_data1.to_csv("./Datos/Datos_analisis_EC_traducidos.csv")

    pagsrange = [str(numero) for numero in range(1, 8)]

    titles = []
    links = []
    dates = []
    texts = []

    for pag in pagsrange:
        url = "https://hydrocarbonscolombia.com/page/" + pag + "/?s=ECOPETROL&start_date&end_date&cate&usefulness"
        try:
            req = Request(url=url)
            response = urlopen(req)
            html = BeautifulSoup(response, "html.parser")
            articles = html.find_all("div", class_="item")

            for article in articles:
                try:
                    if 'active' in article['class']:
                        continue
                    else:
                        pass
                    title_element = article.find('h4')

                    if title_element:
                        title = title_element.a.text.strip()
                        link = title_element.a['href']
                    else:
                        title = "nana"
                        link = "nana"

                    text_element = article.find('div', class_='newsnippet')
                    try: 
                        if text_element:
                            text = text_element.p.text.strip() 
                        else:
                            text = "nana"
                    except: 
                        pass  
                    
                    date_element = article.find('div', class_='col-md-8')
                    if date_element:
                        date = date_element.span.text.strip() 
                    else:
                        date = "nana"

                    titles.append(title)
                    links.append(link)
                    dates.append(date)
                    texts.append(text)
                    time.sleep(2)
                except:
                    pass

        except HTTPError as e:
            if e.code == 404:
                continue
            else:
                continue

    data2 = pd.DataFrame({"Date": dates, "Title": titles, "Link": links,"Headline": texts, "Article": texts})

    # Limpieza inicial
    data2['Article'] = data2['Article'].str.replace(r'\[[^\]]*\]', '') 
    data2['Article'] = data2['Article'].str.replace(r'\n', ' ')  
    data2['Article'] = data2['Article'].str.strip()  
    data2['Headline'] = data2['Headline'].str.replace(r'\[[^\]]*\]', '') 
    data2['Headline'] = data2['Headline'].str.replace(r'\n', ' ')  
    data2['Headline'] = data2['Headline'].str.strip()  
    data2['Title'] = data2['Title'].str.replace(r'\[[^\]]*\]', '') 
    data2['Title'] = data2['Title'].str.replace(r'\n', ' ')  
    data2['Title'] = data2['Title'].str.strip()  

    data2["Source"] = "Hydrocarbons"

    data2['Date'] = data2['Date'].apply(lambda x: parser.parse(x, fuzzy=True) if pd.notnull(x) else None)

    #data2.to_csv("./Hydrocarbons.csv", index=False)

    old_data2 = pd.read_csv("./Datos/EC Hydrocarbons.csv")
    new_data2 = pd.concat([old_data2,data2], ignore_index=True).drop_duplicates(subset=["Link"])
    #new_data2["Date"] = pd.to_datetime(new_data2["Date"])
    #new_data2 = new_data2.sort_values(by="Date")
    new_data2.to_csv("./Datos/EC Hydrocarbons.csv")

    # Joining dataframes
    old_final_data = pd.read_csv("./Datos/Datos_analisis_EC_traducidos.csv")
    old_final_data = old_final_data[["Date","Title","Link","Headline","Article","Source"]]
    converted_dates = pd.to_datetime(old_final_data["Date"], format='%Y-%m-%d', errors='coerce')
    mask = converted_dates.notnull()
    old_final_data.loc[mask, "Date"] = converted_dates[mask]
    old_final_data = old_final_data[(old_final_data != 'na') & (old_final_data != 'nana')].dropna()
    new_final_data = pd.concat([old_final_data,new_data1,new_data2], ignore_index=True).drop_duplicates(subset=["Link"])
    new_final_data = new_final_data[["Date","Title","Link","Headline","Article","Source"]]
    new_final_data= new_final_data[(new_final_data != 'na') & (new_final_data != 'nana')].dropna()
    converted_dates = pd.to_datetime(new_final_data["Date"], format='%Y-%m-%d', errors='coerce')
    mask = converted_dates.notnull()
    new_final_data.loc[mask, "Date"] = converted_dates[mask]
    new_final_data.to_csv("./Datos/Datos_analisis_EC_traducidos.csv")