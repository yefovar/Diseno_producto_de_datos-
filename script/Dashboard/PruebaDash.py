#!/usr/bin/env python
# coding: utf-8

import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_table
import pandas as pd
#from flask import Flask
import plotly.graph_objs as go
import plotly.express as px
import plotly.figure_factory as ff
from dash.dependencies import Input, Output


predicciones_modelo = pd.read_csv('predicciones_modelo.csv', sep = '\t')
predicciones_modelo = pd.DataFrame(predicciones_modelo)
predicciones_mensual = pd.read_csv('predicciones_mes_4_ano_2020.csv', sep="\t", header=None)

predicciones_modelo.columns = ['Mes', 'Hora', 'Delegacion', 'Dia semana', 'Tipo de entrada', 'Tipo de Incidente', 'Año', 'Prob. etiqueta 0', 'Prob. etiqueta 1', 'Etiqueta']
predicciones_mensual.columns = ['Mes', 'Hora', 'Delegacion', 'Dia semana', 'Tipo de entrada', 'Tipo de Incidente', 'Año', 'Prob. etiqueta 0', 'Prob. etiqueta 1', 'Etiqueta']

predicciones_modelo.insert(0,'Datos', 'Historicos')
predicciones_mensual.insert(0,'Datos', 'Live')

#'https://www.w3schools.com/w3css/4/w3.css'
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css' ]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


#Tabla de predicciones
def tabla_predicciones(df):
    df_predict = df[['Mes', 'Hora', 'Dia semana', 'Delegacion', 'Tipo de entrada', 'Tipo de Incidente', 'Prob. etiqueta 0', 'Prob. etiqueta 1', 'Etiqueta']].sort_values(['Hora','Prob. etiqueta 1'], ascending=["True", "False"]).round(2)
    tabla_predict = dash_table.DataTable(id='tabla-predicciones',
                                         columns=[{"name": i, "id": i} for i in df_predict.columns],
                                         data=df_predict.to_dict('records'),
                                         fixed_rows={'headers': True},
                                         page_size=15,  # pagination recommended form +1k rows
                                         style_header={'backgroundColor':colors['title'],'fontWeight':'bold','align':'left',
                                                       'color': '#ffffff', 'fontSize':14},
                                         style_data_conditional=[{'if': {'row_index':'odd'},
                                                                  'backgroundColor':colors['background']}],
                                         style_cell={'fontSize':12},
                                         style_cell_conditional=[{'if': {'column_id': 'Delegacion'},
                                                                       'width': '15%'},
                                                                 {'if': {'column_id': 'Tipo de entrada'},
                                                                       'width': '15%'},
                                                                 {'if':{'column_id': 'Prob. etiqueta 0'},
                                                                       'width': '13%'},
                                                                 {'if':{'column_id': 'Prob. etiqueta 1'},
                                                                       'width': '13%'},
                                                                 {'if':{'column_id': 'Etiqueta'},
                                                                       'width': '8%'}],
                                         style_table={'overflowY': 'scroll', 'overflowX': 'auto'}
                                   )
    return tabla_predict
    


#Df para grafica de Dropdown
df = pd.concat([predicciones_modelo, predicciones_mensual], axis=0)
available_indicators = df['Delegacion'].unique()

#Df para Número de etiquetas positivas vs delegacion
df1 = df.groupby(['Datos','Delegacion']).mean()*100
df1 = df1.reset_index(level=[0,1])
df1.rename(columns = {'Etiqueta':'Porcentaje'}, inplace=True)
fig1 = px.bar(df1, x='Delegacion', y="Porcentaje", color='Datos', barmode='group',
             height=450)
fig1.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', xaxis_tickangle=-90)

colors = {
    'background': '#d8ddd9',
    'title': '#06416e',
    'text': '#1a1b1b'
}


app.layout = html.Div(style={'backgroundColor': colors['background']},                       
            children=[
                      html.H1(children="Incidentes Viales reportados al C5 en la CDMX",
                              style={'textAlign': 'center', 'color': colors['title'],'fontWeight':'bold'}
                              ),
                      html.H4(children="Dashboard para monitoreo del modelo",
                              style={'textAlign': 'center', 'color': colors['text'],'padding-bottom':'0px', 'fontSize':20}
                             ),
                      html.Div([
                                dcc.Markdown("Se diseño un modelo que ayuda a predecir los incidentes de emergencias **reales**, asignados a la etiqueta 1, con el fin de mejorar la asignación de los servicios de emergencia de la Ciudad de México (grúas, patrullas, ambulancias, médicos, etc.)."),
                                dcc.Markdown("#### 1. Tabla de Predicciones")
                                ], style={'marginLeft': 10, 'marginRight': 10, 'marginTop': 10, 'marginBottom': 10, 
                                          'backgroundColor': colors['background'],
                                          'padding': '6px 6px 0px 8px'}
                                ),
                      html.Div([tabla_predicciones(predicciones_mensual)],
                               style={'margin-left': 'auto','margin-right': 'auto','padding':'10px 0px 10px 10px'}
                               ),
                      html.Div(dcc.Markdown("#### 2. Gráficas de predicciones"),
                               style={'marginLeft': 10, 'marginRight': 10, 'marginTop': 10, 'marginBottom': 0, 
                                      'backgroundColor': colors['background'],
                                      'padding': '6px 6px 0px 0px'}),
                      html.Div([
                                html.Div([html.Br(),
                                          html.H5('Porcentaje de etiquetas positivas'),
                                          html.Br(),html.Br(),html.Br(),
                                          dcc.Graph(figure=fig1)
                                         ], #className='w3-container w3-display-bottomleft w3-half height:100% w3-blue',
                                           style={'marginLeft': 10, 'marginRight': 10,
                                                  'marginTop': 10, 'marginBottom': 10,
                                                  'width': '48%', 'display': 'inline-block', 'height': '400px'}
                                         ),
                                html.Div([
                                          html.H5('Comparación de distribuciones de las etiquetas'),      
                                          html.Div([
                                                    dcc.Dropdown(id='xaxis-delegacion',
                                                                 options=[{'label': i, 'value': i}
                                                                         for i in available_indicators],
                                                                 value='cuauhtemoc'
                                                                 ),
                                                    dcc.RadioItems(id='xaxis-etiqueta',
                                                                   options=[{'label': i, 'value': i} 
                                                                            for i in ['Prob. etiqueta 1', 'Prob. etiqueta 0']],
                                                                   value='Prob. etiqueta 1',
                                                                   labelStyle={'display': 'inline-block'}
                                                                   )
                                            ]),
                                  dcc.Graph(id='histogram-graph'),
                                  ], #className='w3-container w3-display-bottomright w3-half w3-red',
                                    style={'marginLeft': 10, 'marginRight': 10,
                                           'marginTop': 10, 'marginBottom': 10,
                                           'width': '48%', 'display': 'inline-block'}
                                  )
                          html.Div(dcc.Markdown("#### 2. Gráficas de predicciones"),
                                   style={'marginLeft': 10, 'marginRight': 10, 'marginTop': 10, 'marginBottom': 0, 
                                      'backgroundColor': colors['background'],
                                      'padding': '6px 6px 0px 0px'}
                                   )
                      ])
                ])

     

    

    
@app.callback(
    Output('histogram-graph', 'figure'),
    [Input('xaxis-delegacion', 'value'),
     Input('xaxis-etiqueta', 'value')]
)
def update_graph(xaxis_delegacion, xaxis_etiqueta):
    dff = df[df['Delegacion'] == xaxis_delegacion]
    
    fig = px.histogram(dff, x=dff[xaxis_etiqueta], color="Datos", histnorm='percent', nbins=50, barmode="overlay",
                   title='Comparación de las distribuciones <br> (Datos históricos vs. Live)',
                   labels={'percent': 'Porcentaje'}
                  )
    fig.update_yaxes(title_text='Porcentaje')
    return fig


    
#GRAFICAS BIAS FAIRNESS    
########### ************************************

app = dash.Dash(__name__)
server = app.server
app.title = 'Incidentes Viales CDMX C5'

df = pd.read_csv('df_bias.csv',sep='\t')

def update_graph1(df):
    
    dff = df
    
    fig=px.bar(df,x='attribute_value',y='for',color='for',
            title='Métrica False Omission Rate por Delegaciones',
               labels={'attribute_value': 'Delegación','for':'Métrica FOR'})
    
    return fig

def update_graph2(df):
    
    dff = df
    
    fig=px.bar(df,x='attribute_value',y='fnr',color='fnr',
            title='Métrica False Negative Rate por Delegaciones',
               labels={'attribute_value': 'Delegación','fnr':'Métrica FNR'})
    
    return fig


fig1=update_graph1(df)
fig2=update_graph2(df)

#Layout de FOR
app.layout = html.Div([
    dcc.Graph(figure=fig1)],
    style={'width': '48%', 'display': 'inline-block'})

#Layout de FNR
app.layout = html.Div([
    dcc.Graph(figure=fig2)],
    style={'width': '48%', 'display': 'inline-block'})

    
    

    
    
    

if __name__ == '__main__':
    app.run_server(debug=True)






