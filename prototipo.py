#bibliotecas
import sqlite3
import csv
import pandas as pd
import geopandas as gpd
import folium
from folium import plugins
from folium.plugins import MousePosition
import branca
import branca.colormap as cm
from branca.colormap import LinearColormap
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
from sklearn.neighbors import KNeighborsRegressor
from scipy.interpolate import griddata
from shapely.geometry import Point
import requests
import time


#apresentação
print('\nProjeto RF Web\n\nAluno:\nBruno Luís Monteiro Bezerra -UNB\n\nProfessor:\nGeorge Sand Leão de França- USP')

#abrindo o banco de dados
banco=sqlite3.connect('database_final.db')
cursor=banco.cursor()
x=0
#loop para as opções
while True:
    while x!=1 and x!=2 and x!=3 and x!=4 and x!=5:
        print('\nQual opção deseja?')
        print('1-Criar uma tabela')
        print('2-Atualizar uma tabela existente')
        print('3-Mostrar dados existentes')
        print('4-Mostrar o mapa com os dados existentes')
        print('5-Sair')
        x=int(input('[1,2,3,4,5]?\n'))
        
    
    if x==1:#opção 1 - criar tabela
        w=2
        while w==2:#loop para opção 1
            n=input('Qual o nome da tabela? (digite [return] se quiser voltar)\n')
            if n!='return':
                m=input('Quais titulos dentro da tabela?\nex: estação, rede, longitude, ...\n')
                print('\n\ntabela: ',n)
                print('titulos :', m)
                print('Está correto? Sim=1, Não=2')
                w=int(input())
                if w==1:
                    cursor.execute("CREATE TABLE "+n+" ("+m+")")#comando para criar tabela
                    print('Tabela criada')
            else:
                w=1
            x=0
    elif x==2:#opção 2 - atualizar tabela
        print('\nQual tabela deseja atualizar?\n')
        cursor.execute("SELECT * FROM sqlite_master WHERE type='table';")#mostra as tabelas
        for linha in cursor.fetchall():
            print(linha[4][13:])
        n=input('Digite apenas o nome da tabela: (digite [return] se quiser voltar)\n')
        if n!='return':
            cursor.execute("SELECT * FROM "+n+";")
            for linha in cursor.fetchall():
                print(linha)
            q=input('\nQual o nome do arquivo?\n')
            ficheiro = open(''+q+'.csv', 'r')#nome do arquivo para atualização
            reader = csv.reader(ficheiro)
            for linha in reader:
                print (linha)
                cursor.execute("INSERT INTO "+n+" VALUES('"+linha[0]+"','"+linha[1]+"','"+linha[2]+"','"+linha[3]+"','"+linha[4]+"','"+linha[5]+"','"+linha[6]+"','"+linha[7]+"','"+linha[8]+"','"+linha[9]+"')")
                banco.commit()#comandos para adicionar na tabela
            print('\nTabela atualizada com sucesso')
        x=0
    elif x==3:#opção 3 -mostrar dados
        w=1
        while w==1:#loop para opção 3
            print('\n')
            cursor.execute("SELECT * FROM sqlite_master WHERE type='table';")
            for linha in cursor.fetchall():
                print(linha[4][13:])#mostra as tabelas
            n=input('\nDigite apenas o nome da tabela: (digite [return] se quiser voltar)\n')
            if n!='return':
                cursor.execute("SELECT * FROM "+n+";")
                for linha in cursor.fetchall():
                    print(linha)#mostra os dados dentro da tabela
                w=int(input('\nGostaria de ver outra tabela?\nSim=1,Não=2\n'))
            else:
                w=2
            x=0
    elif x==4:#opção 4 - mostrar mapa
        w=1
        while w==1:#loop para opção 4
            print('\n')
            cursor.execute("SELECT * FROM sqlite_master WHERE type='table';")
            for linha in cursor.fetchall():
                print(linha[4][13:])#mostrar tabelas para escolha
            n=input('\nDigite apenas o nome da tabela: (digite [return] se quiser voltar)\n')
            if n!='return':
                cursor.execute("SELECT * FROM "+n+";")
                df = pd.read_sql("SELECT * FROM "+n+"",banco)
                df.to_csv("saida.csv", index=False)#cria um arquivo de saida com todos os dados que serão impressos
                df = pd.read_csv("saida.csv")#lê o arquivo de saida
                
                
                latitudes = df['Long'].values
                longitudes = df['Lat'].values
                valores = df['H'].values
                erros = df['DesvH'].values
                elev=df['Elev'].values

                # Substituir "-" por NaN na coluna 'VpVs'
                df['VpVs'] = df['VpVs'].replace('-', np.nan)

                # Remover linhas com valores NaN nas colunas 'VpVs', 'Long' e 'Lat'
                df.dropna(subset=['VpVs'], inplace=True)
                df['VpVs'] = pd.to_numeric(df['VpVs'], errors='coerce')

                #Pegar os valores da coluna 'VpVs' após a remoção dos valores "-"
                valoresVp = df['VpVs'].values
                latv = df['Long'].values
                lonv = df['Lat'].values
                elevv = df ['Elev'].values

                # Carregar o arquivo GeoJSON dos limites do Brasil
                geojson_path = 'data/limite_brasil.geojson'
                gdf_brasil = gpd.read_file(geojson_path)

                # Obter os limites do Brasil
                x_min, y_min, x_max, y_max = gdf_brasil.total_bounds

                # Definir o número de pontos na grade
                num_points = 100

                # Criar uma malha irregular seguindo os limites do Brasil
                grid_points = []
                for x in np.linspace(x_min, x_max, num_points):
                    for y in np.linspace(y_min, y_max, num_points):
                        point = Point(x, y)
                        if gdf_brasil.geometry.apply(lambda g: g.intersects(point)).any():
                            grid_points.append(point)

                # Criar a grade de pontos a partir da malha irregular
                grid_lat = [point.y for point in grid_points]
                grid_lon = [point.x for point in grid_points]


                def get_elevation(latitude, longitude):
                    base_url = "https://api.open-elevation.com/api/v1/lookup"
                    params = {
                        "locations": f"{latitude},{longitude}",
                        "format": "json",
                    }

                    try:
                        response = requests.get(base_url, params=params)
                        data = response.json()
                        if "results" in data and data["results"]:
                            elevation = data["results"][0]["elevation"]
                            return elevation
                        else:
                            print("Dados de elevação não encontrados.")
                            return None
                    except Exception as e:
                        print(f"Erro ao acessar a API: {e}")
                        return None

                # Função para obter a elevação com tentativas repetidas em caso de erro
                def get_elevation_with_retry(lat, lon, max_attempts=3, retry_delay=1):
                    attempts = 0
                    while attempts < max_attempts:
                        elevation = get_elevation(lat, lon)
                        if elevation is not None:
                            return elevation
                        attempts += 1
                        time.sleep(retry_delay)  # Espere por um tempo antes de tentar novamente
                    print('falhou')
                    return None  # Retorna None se todas as tentativas falharem

                grid_elev=[]
                for i in range(len(grid_lat)):
                    elev_np = get_elevation_with_retry(grid_lat[i], grid_lon[i])
                    if elev_np is not None:
                        grid_elev.append(elev_np)
                        print(elev_np,i)
                

                #realizar a interpolação usando k-vizinhos mais próximos
                knn = KNeighborsRegressor(n_neighbors=3)
                knn.fit(np.column_stack((latitudes, longitudes, elev)), valores)
                grid_h = knn.predict(np.column_stack((grid_lat, grid_lon, grid_elev)))
                #interpolação para VpVs
                knn.fit(np.column_stack((latv, lonv, elevv)), valoresVp)
                grid_Vp = knn.predict(np.column_stack((grid_lat, grid_lon, grid_elev)))



                #criar um novo mapa para exibir a interpolação
                arq_gj="data/limite_brasil.geojson"
                arq_bacias="data/limite_bacias.geojson"
                arq_mun="data/brazil-states.geojson"
                stl= lambda x:{'color':'black', 'fillOpacity' : 0, 'weight': 0.8}
                mapa_interp = folium.Map(location=[np.mean(latitudes), np.mean(longitudes)], zoom_start=4,control_scale=True)
                folium.TileLayer(tiles='cartodbpositron').add_to(mapa_interp)
                folium.TileLayer(tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
                                attr='"" (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)',
                                name='OpenTopoMap').add_to(mapa_interp)


                over_h = folium.FeatureGroup(name='Interpolação de H (km)')
                over_vp=folium.FeatureGroup(name='Interpolação de Vp/Vs', show=False)
                mun_layer=folium.GeoJson(arq_mun, name="Limite dos Municípios",style_function=stl, show=False)
                brasil_layer=folium.GeoJson(arq_gj, name="Limite do Brasil",style_function=stl)
                bacia_layer=folium.GeoJson(arq_bacias, name="Limite de Bacias sedimentares",style_function=stl, show=False)
                MousePosition().add_to(mapa_interp)




                #adicionar marcadores no mapa com os valores da estação
                for est, lat, lon, elev, h, desv_h, vpvs, desv_vpvs in zip(df.est.values, df.Long.values, df.Lat.values, df.Elev.values, df.H.values, df.DesvH.values, df.VpVs.values, df.DesvVpVs.values):
                    Hstr = str(h)
                    Estr = str(elev)
                    DHstr = str(desv_h)
                    Vstr = str(vpvs)
                    DVstr = str(desv_vpvs)
                    colormap = cm.LinearColormap(colors=['darkblue', 'blue', 'cyan', 'yellow', 'orange', 'red'], vmin=min(df.H.values), vmax=max(df.H.values), caption='[Km]')
                    color = colormap(h)
                    folium.Marker(location=[lat, lon],
                                     icon=folium.CustomIcon(icon_image='data/btriangle.png', icon_size=(20, 20)),
                                     popup=('Estação:' + est + '\nElev:' + Estr + '\nH:' + Hstr + '+-' + DHstr + '\nVp/Vs:' + Vstr + '+-' + DVstr + '\n')).add_to(mapa_interp)

                #adicionar marcadores no mapa com os valores interpolados de 'H'
                for lat, lon, h, ele in zip(grid_lat, grid_lon, grid_h, grid_elev):
                    colormap_h = cm.LinearColormap(colors=['darkblue', 'blue', 'cyan', 'yellow', 'orange', 'red'], vmin=min(df.H.values), vmax=max(df.H.values), caption='Espessura Crustal (km)')
                    color = colormap_h(h)
                    folium.Circle(location=[lat, lon], radius=10000, color=None, fill=True, fill_color=color, fill_opacity=0.8,
                             popup='H: {:.2f} \n Elev.: {:.0f}'.format(h, ele)).add_to(over_h)
                mapa_interp.add_child(colormap_h)
                #colormap_h.add_to(over_h)

                #adicionar marcadores no mapa com os valores interpolados de 'VpVs'
                for lat, lon, vpvs, ele in zip(grid_lat, grid_lon, grid_Vp, grid_elev):
                    colormap_vp = cm.LinearColormap(colors=['darkblue', 'blue', 'cyan', 'yellow', 'orange', 'red'], vmin=min(df.VpVs.values), vmax=max(df.VpVs.values), caption='Vp/Vs')
                    color = colormap_vp(vpvs)
                    folium.Circle(location=[lat, lon], radius=10000, color=None, fill=True, fill_color=color, fill_opacity=0.8,
                             popup='Vp/Vs: {:.2f} \n Elev.: {:.0f} '.format(vpvs, ele)).add_to(over_vp)

                mapa_interp.add_child(mun_layer)
                mapa_interp.add_child(bacia_layer)
                mapa_interp.add_child(brasil_layer)    
                mapa_interp.add_child(colormap_vp)
                mapa_interp.add_child(over_h)
                mapa_interp.add_child(over_vp)
                folium.LayerControl().add_to(mapa_interp)
                #exibir o mapa com a interpolação
                display(mapa_interp)


                    
                w=int(input('\nGostaria de ver outro mapa?\nSim=1,Não=2\n'))
            else:
                w=2
        x=0
        
    elif x==5:#opção de saida do programa
        print('\nObrigado')
        break
    
    else:
        print('\nDigite um número válido')
