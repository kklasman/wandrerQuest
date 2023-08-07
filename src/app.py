import dash
from dash import Dash, html, dcc, Input, Output, callback, ctx, State
from dash.dash_table import DataTable, FormatTemplate
from dash.dash_table.Format import Format, Scheme, Trim
from dash.exceptions import PreventUpdate

import dash_bootstrap_components as dbc

import collections
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objs as go
import warnings
import base64

warnings.simplefilter(action='ignore', category=FutureWarning)

app = Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[
    dbc.themes.SPACELAB, dbc.icons.FONT_AWESOME])
server = app.server

# app.config.supress_callback_exceptions = True

percentage = FormatTemplate.percentage(2)
fixed = Format(precision=2, scheme=Scheme.fixed)

my_color_scale = ['white', 'gold', 'red']

latitude = 44.18294737
longitude = -69.25990211
zoom = 7.75

summary_columns = [
    dict(id='County', name='County'),
    dict(id='Total (mi)', name='Total Miles', type='numeric', format=fixed),
    dict(id='25 Pct', name='25% Target Miles', type='numeric', format=fixed),
    dict(id='Actual Pct', name='Wandrer Pct', type='numeric', format=percentage),
    dict(id='Actual (mi)', name='Miles Ridden', type='numeric', format=fixed),
    dict(id='Total Towns', name='Total Towns'),
    dict(id='geoid', name='Geo Id')
]


def create_onedrive_directdownload(onedrive_link):
    print('\nfunction create_onedrive_directdownload')
    data_bytes64 = base64.b64encode(bytes('https://' + onedrive_link, 'utf-8'))
    data_bytes64_String = data_bytes64.decode('utf-8').replace('/', '_').replace('+', '-').rstrip("=")
    resultUrl = f"https://api.onedrive.com/v1.0/shares/u!{data_bytes64_String}/root/content"
    return resultUrl


def load_state_summary(selected_state):
    print('\nfunction load_state_summary')
    # onedrive_link = "https://1drv.ms/x/s!An0k-SnslkINyjUdvZ4llcQGIT5V?e=hvKTIq"
    df_state = df_StateWQData.loc[df_StateWQData.State == selected_state]
    link = df_state.iloc[0]['StateOneDriveLink']
    countyCount = df_state.iloc[0]['CountyCount']
    onedrive_direct_link = create_onedrive_directdownload(link)

    # print('\nloading df_summary...')
    if selected_state == 'New England':
        df_summary = pd.read_excel(onedrive_direct_link,
                                   usecols=[0, 1, 3, 5, 8, 9, 21, 29], nrows=countyCount)
    else:
        df_summary = pd.read_excel(onedrive_direct_link,
                                   usecols=[0, 2, 4, 7, 8, 20, 28], nrows=countyCount)
    # print('\df_summary:')
    # print(df_summary)

    return df_summary


def get_county_json(chosen_state):
    print('\nfunction get_county_json for state ' + chosen_state)
    if chosen_state == 'Maine':
        r = open('../geojsonFiles/Maine_County_Boundaries.geojson.json')
        # r = open('geojsonFiles/New_England_County_Boundaries.geojson.json')
    elif chosen_state == 'New Hampshire':
        r = open('../geojsonFiles/New_Hampshire_County_Boundaries.geojson.json')
    else:
        r = open('../geojsonFiles/New_England_County_Boundaries.geojson.json')

    counties = json.load(r)
    return counties


def create_state_map(chosen_state, df_cleaned_summary):
    print("\nfunction create_state_map: " + chosen_state)
    df_state = df_StateWQData.loc[df_StateWQData.State == chosen_state]

    latitude = df_state.iloc[0]['cLatitude']
    longitude = df_state.iloc[0]['cLongitude']
    zoom = df_state.iloc[0]['Zoom']
    geoidPropertyName = df_state.iloc[0]['GeoidPropertyName']
    # print('geoidPropertyName: ' + geoidPropertyName)

    counties = get_county_json(chosen_state)

    counties['features'] = [f for f in counties['features'] if
                            f['properties'][geoidPropertyName] in df_cleaned_summary[geoidPropertyName].unique()]

    fig = px.choropleth_mapbox(df_cleaned_summary, geojson=counties, locations=geoidPropertyName, color='Actual Pct',
                               color_continuous_scale=my_color_scale,
                               mapbox_style="carto-positron",
                               zoom=zoom,
                               center={"lat": latitude, "lon": longitude},
                               opacity=0.75,
                               range_color=[0, .4],
                               hover_data=['County'],
                               height=700
                               )
    fig = fig.update_layout(margin={"r": 1, "t": 1, "l": 1, "b": 1})
    return fig


def create_region_map():
    selected_state = 'New England'

    df_summary = load_state_summary(selected_state)
    # print(df_summary.County.unique())

    # clean data for display in table
    df_cleaned_summary = df_summary.dropna()
    cleaned_summary_json = df_cleaned_summary.to_json(orient='split')

    # create state map
    region_map = create_state_map(selected_state, df_cleaned_summary)
    return region_map


def getStateWQData():
    print('function getStateWQData')
    df = pd.read_excel('../data/StateWQData.xlsx')
    # usecols=[0, 2, 4, 7, 8, 20, 28], nrows=16)
    print('\ndf:')
    # print(df)
    return df

df_StateWQData = getStateWQData()

states = df_StateWQData.State.unique()
print(states)

dict_state = {}


card_data = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H4(id='data_card_header', children='This card contains data', className='card-title text-center'),
                # dbc.CardImg(src="assets/20200926-12.jpg", top=True, bottom=False,
                #             title="Image by Kevin Klasman", alt='Select a location to browse'),
                # DataTable(id='table', data=[], columns=summary_columns, page_size=20)
                # html.Div(id='table', children={})
                html.Div(id='table'),
                # DataTable(id='table'),
                # dbc.Alert('Table cell clicked', id='out')
            ]
        )
    ])


card_main_form = dbc.Card(
    dbc.CardBody(
        dbc.Form([
            html.H5("Select a location to browse", className="card-title"),
            dbc.Row([
                dbc.Label("Region", width='auto'),
                dbc.Col(
                    dcc.Dropdown(options=states, id='state_dropdown', searchable=False, style={"color": "#000000"}),
                    xs=9, sm=8, md=10, lg=3, xl=2),
                dbc.Label("County", width='auto'),
                dbc.Col(dcc.Dropdown(options={}, id='county_dropdown', searchable=False,
                                     style={"color": "#000000"}),
                        xs=9, sm=4, md=5, lg=3, xl=2),
                dbc.Label("Town", width='auto'),
                dbc.Col(dcc.Dropdown(id='town_dropdown', options={}, searchable=False, style={"color": "#000000"}),
                        xs=9, sm=4, md=4, lg=3, xl=4),
            ]),
            dbc.Row([
                dbc.Col(dcc.Store(id='summary_data')),
                dbc.Col(dcc.Store(id='county_data')),
                dbc.Col(dcc.Store(id='state_geometry_json')),
                dbc.Col(dcc.Store(id='state_map_cache')),
                dbc.Col(dcc.Store(id='state_table_cache')),
                dbc.Col(dcc.Store(id='county_map_cache')),
                dbc.Col(dcc.Store(id='town_table_cache')),
            ])
        ],
        ),
    ),
    color="dark",  # https://bootswatch.com/default/ for more card colors
    inverse=True,  # change color of text (black or white)
    outline=False,  # True = remove the block colors from the background and header
)

card_graph = dbc.Card(
    # dcc.Graph(id='my_choropleth', figure=usa_base_map(), className="h-100"),
    dcc.Graph(id='my_choropleth', figure=create_region_map(), className="h-100"),
    body=True, color="secondary",
    # style={"height": 875},
    className="p-4 bg-secondary",
)


app.layout = dbc.Container([
    dbc.Row([dbc.Col(html.H2("Browse WandrerQuest Data by Map", className='text-center bg-primary text-white p-2'))
             ]),
    dbc.Row([dbc.Col(card_main_form, className="mx-1")
             ]),
    dbc.Row([
        # dbc.Col(card_graph, className="mt-1 mb-1", xs=12, sm=12, md=12, lg=6, xl=6,
        #         # align='center', style={"height": "100vh"}
        #         ),
        dbc.Col(dcc.Loading(children=[card_graph], fullscreen=False), className="mt-1 mb-1", xs=12, sm=12, md=12, lg=6, xl=6,),
        # dbc.Col(card_data, className="m-1", xs=12, sm=12, md=12, lg=5, xl=5)
        dbc.Col(dcc.Loading(children=[card_data], fullscreen=False), className="m-1", xs=12, sm=12, md=12, lg=5, xl=5)
    ],
        style={'flexGrow': '1'}
        # style={'overflowX': 'scroll'}
    ),
    dbc.Row([dbc.Col(html.H2("WandrerQuest footer", className='text-center bg-primary text-white p-2'))
             ]
            ),
],
    fluid=True,
    style={'height': '100vh', 'display': 'flex', 'flexDirection': 'column'}
)


def load_county_by_name(selected_state, county_name, summary_data):
    print('\nfunction load_county_by_name')
    if selected_state:
        print('...selected_state: ' + str(selected_state))

    if county_name:
        print('...county_name: ' + str(county_name))
    else:
        return []

    df_wq = df_StateWQData.loc[df_StateWQData['State'] == selected_state]
    # link = df_wq['StateOneDriveLink']
    link = df_wq.iloc[0]['StateOneDriveLink']
    # link = df_wq.iloc[0]['CountyOneDriveLink']
    onedrive_direct_link = create_onedrive_directdownload(link)

    df_summary = pd.read_json(summary_data, orient='split')
    row_count = int(df_summary.loc[df_summary['County'] == county_name]['Total Towns'])
    df = pd.read_excel(onedrive_direct_link, sheet_name=county_name,
                       # usecols=[0, 1, 2, 4, 7, 8, 27],
                       usecols=[0, 1, 2, 4, 7, 8, 18, 19],
                       nrows=row_count)
    # df = pd.read_excel(onedrive_direct_link, sheet_name=county_name)

    df['id'] = df['Town']

    return df.sort_values('Town')


def load_town_boundaries(selected_state, county_name, summary_data):
    print('\nfunction load_town_boundaries')
    if selected_state:
        print('...selected_state: ' + str(selected_state))

    if county_name:
        print('...county_name: ' + str(county_name))
    else:
        return []

    # me_onedrive_link = "https://1drv.ms/x/s!An0k-SnslkINyjUdvZ4llcQGIT5V?e=hvKTIq"
    # me_onedrive_direct_link = create_onedrive_directdownload(me_onedrive_    link)
    df_wq = df_StateWQData.loc[df_StateWQData['State'] == selected_state]
    # link = df_wq['StateOneDriveLink']
    link = df_wq.iloc[0]['TownBoundariesExcelOneDriveLink']
    onedrive_direct_link = create_onedrive_directdownload(link)

    df_summary = pd.read_json(summary_data, orient='split')
    row_count = int(df_summary.loc[df_summary['County'] == county_name]['Total Towns'])
    df = pd.read_excel(onedrive_direct_link, sheet_name=county_name,
                       # usecols=[0, 1, 2, 4, 7, 8, 27],
                       # usecols=[0, 1, 2, 4, 7, 8, 18, 19],
                       nrows=row_count)
    # df = pd.read_excel(onedrive_direct_link, sheet_name=county_name)

    df['id'] = df['Town']

    return df.sort_values('Town')




def blank_figure():
    print('\nfunction blank_figure')
    fig = go.Figure(go.Scatter(x=[], y=[]))
    fig.update_layout(template=None)
    fig.update_xaxes(showgrid=False, showticklabels=False, zeroline=False)
    fig.update_yaxes(showgrid=False, showticklabels=False, zeroline=False)
    return fig


def usa_base_map():
    print('\nfunction blank_figure')

    fig = px.choropleth_mapbox(
        # fips=fips,
        # values=values,
        mapbox_style="carto-positron",
        center={"lat": 40.078015, "lon": -94.918191},
        zoom=3
        # binning_endpoints=[14348, 63983, 134827, 426762, 2081313], colorscale=colorscale,
        # county_outline={'color': 'rgb(255,255,255)', 'width': 0.5}, round_legend_values=True,
        # legend_title='Population by County', title='California and Nearby States'
    )
    # fig = fig.update_layout( margin={"r": 1, "t": 1, "l": 1, "b": 1})
    return fig


# def get_center_coords(county_objects, oid, locations_field):
#     print('\nfunction get_center_coords')
#     max_lat = 0
#     min_lat = 0
#     max_lon = 0
#     min_lon = 0
#
#     for feature in county_objects['features']:
#         if int(feature['properties'][locations_field]) == oid:
#             # print(feature['geometry']['coordinates'])
#             # print(feature['geometry']['coordinates'][0])
#             for coord in feature['geometry']['coordinates'][0]:
#                 # print(feature['geometry']['coordinates'][0][0])
#                 # print(coord)
#                 if max_lat == 0:
#                     max_lat = coord[1]
#                 elif coord[1] > max_lat:
#                     max_lat = coord[1]
#                 if min_lat == 0:
#                     min_lat = coord[1]
#                 elif coord[1] < min_lat:
#                     min_lat = coord[1]
#
#                 if max_lon == 0:
#                     max_lon = coord[0]
#                 elif coord[0] > max_lon:
#                     max_lon = coord[0]
#                 if min_lon == 0:
#                     min_lon = coord[0]
#                 elif coord[0] < min_lon:
#                     min_lon = coord[0]
#
#     avglat = (max_lat + min_lat) / 2
#     avglon = (max_lon + min_lon) / 2
#     return avglat, avglon


def get_center_coords_from_town_json(town_json, oid, locations_field):
    print('\nfunction get_center_coords_from_town_json')
    max_lat = 0
    min_lat = 0
    max_lon = 0
    min_lon = 0

    for coord in town_json['geometry']['coordinates'][0]:
        # print(feature['geometry']['coordinates'][0][0])
        # print(coord)
        if max_lat == 0:
            max_lat = coord[1]
        elif coord[1] > max_lat:
            max_lat = coord[1]
        if min_lat == 0:
            min_lat = coord[1]
        elif coord[1] < min_lat:
            min_lat = coord[1]

        if max_lon == 0:
            max_lon = coord[0]
        elif coord[0] > max_lon:
            max_lon = coord[0]
        if min_lon == 0:
            min_lon = coord[0]
        elif coord[0] < min_lon:
            min_lon = coord[0]

    avgLat = (max_lat + min_lat) / 2
    avgLon = (max_lon + min_lon) / 2
    return avgLat, avgLon



def create_county_map(df_towns, selected_state, selected_county, town_json):
    print("\nfunction create_county_map")

    if not selected_county:
        print('...returning from create_county_map early because county not chosen')
        return

    print('...county_dropdown: ' + selected_county)
    # print('town_dropdown: ' + df_towns)
    # print(df)

    # print(df_towns)

    # Some towns have multiple rows, but only the most important will have 'Y'
    primary_town = df_towns[df_towns['Primary'] == 'Y']
    primary_town.reset_index(inplace=True)  # ensure the only row remaining has id = 0

    oid = int(primary_town.OBJECTID[0])
    print(oid)

    county_latitude = float(df_StateWQData[
                                (df_StateWQData['State'] == selected_state) & (
                                        df_StateWQData['CountyName'] == selected_county)].cLatitude)
    county_longitude = float(df_StateWQData[
                                 (df_StateWQData['State'] == selected_state) & (
                                         df_StateWQData['CountyName'] == selected_county)].cLongitude)
    county_zoom = float(df_StateWQData[
                     (df_StateWQData['State'] == selected_state) & (
                             df_StateWQData['CountyName'] == selected_county)].Zoom)

    dff = df_StateWQData[
        (df_StateWQData['State'] == selected_state) & (df_StateWQData['CountyName'] == selected_county)]
    locations_field = dff.iloc[0]['GeoidPropertyName']

    fig = px.choropleth_mapbox(df_towns, geojson=town_json, locations=locations_field, color='Actual Pct',
                               color_continuous_scale=my_color_scale,
                               mapbox_style="carto-positron",
                               zoom=county_zoom,
                               center={"lat": county_latitude, "lon": county_longitude},
                               opacity=0.75,
                               range_color=[0, 1],
                               hover_data=['County', 'Town']
                               )
    fig = fig.update_layout(margin={"r": 1, "t": 1, "l": 1, "b": 1})
    return fig


def create_county_map_from_state_data(df_towns, selected_state, selected_county, town_json):

    if not selected_county:
        print('...returning from create_county_map_from_state_data early because county not chosen')
        return

    print('\nfunction create_county_map_from_state_data for ' + selected_county)
    print('...county_dropdown: ' + selected_county)
    # print('town_dropdown: ' + df_towns)
    # print(df)

    # print(df_towns)

    county_latitude = float(df_StateWQData[
                                (df_StateWQData['State'] == selected_state) & (
                                        df_StateWQData['CountyName'] == selected_county)].cLatitude)
    county_longitude = float(df_StateWQData[
                                 (df_StateWQData['State'] == selected_state) & (
                                         df_StateWQData['CountyName'] == selected_county)].cLongitude)
    zoom = float(df_StateWQData[
                     (df_StateWQData['State'] == selected_state) & (
                             df_StateWQData['CountyName'] == selected_county)].Zoom)

    dff = df_StateWQData[
        (df_StateWQData['State'] == selected_state) & (df_StateWQData['CountyName'] == selected_county)]
    locations_field = dff.iloc[0]['GeoidPropertyName']
    print('...locations_field: ' + locations_field)

    fig = px.choropleth_mapbox(df_towns, geojson=town_json, locations=locations_field, color='Actual Pct',
                               color_continuous_scale=my_color_scale,
                               mapbox_style="carto-positron",
                               zoom=zoom,
                               center={"lat": county_latitude, "lon": county_longitude},
                               opacity=0.75,
                               range_color=[0, 1],
                               hover_data=['County', 'Town']
                               )
    fig = fig.update_layout(margin={"r": 1, "t": 1, "l": 1, "b": 1})
    return fig



def get_town_json_for_state(chosen_state):
    print('function get_town_json_for_state ' + chosen_state)
    if chosen_state == 'Maine':
        r = open('../geojsonFiles/Maine_Town_and_Townships_Boundary_Polygons_Feature.json')
        # r = open('New_England_County_Boundaries.geojson.json')
    elif chosen_state == 'New Hampshire':
        # r = open('../geojsonFiles/New_Hampshire_County_Boundaries.geojson.json')
        r = open('../geojsonFiles/New_Hampshire_Political_Boundaries_4.json')
    else:
        r = open('../geojsonFiles/New_England_County_Boundaries.geojson.json')

    counties = json.load(r)
    return counties




@callback(Output('county_dropdown', 'value'),
          # State('county_dropdown', 'value'),
          State('state_table_cache', 'data'),
          Input('state_table', 'active_cell'))
def state_table_cell_clicked(active_table, active_cell):
    if not active_cell:
        return dash.no_update

    print('\ncallback state_table_cell_clicked')
    row = active_cell['row']
    print(active_cell)
    county = active_table['props']['data'][row]['County']
    print('county: ' + county)
    return county


@callback(Output('town_dropdown', 'value'),
          # State('county_dropdown', 'value'),
          State('town_table_cache', 'data'),
          Input('town_table', 'active_cell'))
def town_table_cell_clicked(active_table, active_cell):
    if not active_cell:
        return dash.no_update

    print('\ncallback town_table_cell_clicked')
    row_id = active_cell['row_id']
    print(active_cell)
    print('...town: ' + row_id)
    return row_id


@callback(Output('county_dropdown', 'value', allow_duplicate=True),
          Output('town_dropdown', 'value', allow_duplicate=True),
          Input('my_choropleth', 'clickData'), prevent_initial_call=True)
def map_clicked(clickData):
    # print(clickData)

    if len(clickData['points'][0]['customdata']) == 1:
        county = clickData['points'][0]['customdata'][0]
        print('\ncallback map_clicked on county ' + county)
        return county, dash.no_update
    else:
        town = clickData['points'][0]['customdata'][1]
        print('\ncallback map_clicked on town ' + town)
        return dash.no_update, town


@callback(Output('county_dropdown', 'options'),
          Output('summary_data', 'data'),
          Output('table', 'children', allow_duplicate=True),
          Output('state_table_cache', 'data'),
          Output('my_choropleth', 'figure', allow_duplicate=True),
          Output('state_geometry_json', 'data'),
          Output('town_dropdown', 'options', allow_duplicate=True),
          Output('state_map_cache', 'data'),
          Output('data_card_header', 'children', allow_duplicate=True),
          Input('state_dropdown', 'value'), prevent_initial_call=True)
# Input('state_dropdown', 'value'), prevent_initial_call='initial_duplicate')
def state_dropdown_clicked(selected_state):
    # print('\ncallback: state_dropdown_clicked...triggered by ' + ctx.triggered_id)
    if not selected_state:
        # print('\ncallback: state_dropdown_clicked: selected_state not provided.')
        # print('...ctx.triggered_id: ' + var)
        return ()

    print('\ncallback: state_dropdown_clicked triggerd by ctx.triggered_id')
    if len(df_StateWQData[df_StateWQData['State'] == selected_state]) > 0:
        df_summary = load_state_summary(selected_state)
        # print(df_summary.County.unique())

        # clean data for display in table
        df_cleaned_summary = df_summary.dropna()
        cleaned_summary_json = df_cleaned_summary.to_json(orient='split')

        # create state map
        state_map = create_state_map(selected_state, df_cleaned_summary)

        # get state geometry json and store
        state_geometry_json = get_town_json_for_state(selected_state)

        table_data = DataTable(
            style_header={'whiteSpace': 'normal', 'height': 'auto', 'fontWeight': 'bold', 'text-align': 'center'},
            columns=summary_columns,
            data=df_cleaned_summary.to_dict('records'),
            # page_size=20,
            style_table={'overflowX': 'scroll'},
            id='state_table'
            )
        return df_summary.County.unique(), cleaned_summary_json, table_data, table_data, state_map, \
            state_geometry_json, {}, state_map, 'WandrerQuest data for the state of ' + selected_state
    else:
        print('...get_counties: state_dropdown: ' + selected_state + ' not coded yet')
        return {}


@callback(Output('town_dropdown', 'options'),
          Output('county_data', 'data'),
          Output('table', 'children', allow_duplicate=True),
          Output('my_choropleth', 'figure', allow_duplicate=True),
          Output('county_map_cache', 'data'),
          Output('data_card_header', 'children', allow_duplicate=True),
          Output('town_table_cache', 'data'),
          Input('county_dropdown', 'value'),
          State('state_dropdown', 'value'),
          State('summary_data', 'data'),
          State('state_geometry_json', 'data'),
          State('state_map_cache', 'data'),
          State('state_table_cache', 'data'),
          State('town_table_cache', 'data'),
          prevent_initial_call=True)
def county_selected(selected_county, selected_state, summary_data, state_geometry_json, cached_state_map,
                    cached_state_table_data, cached_town_table_data):
    print('\ncallback county_selected, called by ' + ctx.triggered_id)

    if not selected_state:
        print('...selected_state not provided.')
        return ()

    if not selected_county:
        print('...selected_county not provided.')
        return {}, [], cached_state_table_data, cached_state_map, dash.no_update, \
            'WandrerQuest data for the state of ' + selected_state, cached_town_table_data

    if selected_state != 'New England':
        df = load_county_by_name(selected_state, selected_county, summary_data)
        df_cleaned_towns = df.dropna()
        cleaned_towns_json = df_cleaned_towns.to_json(orient='split')

        town_columns = [
            dict(id='State', name='State'),
            dict(id='County', name='County'),
            dict(id='Town', name='Town'),
            dict(id='Total (mi)', name='Total Miles', type='numeric', format=fixed),
            dict(id='25 Pct', name='Wandrer Target', type='numeric', format=fixed),
            dict(id='Actual Pct', name='Actual Pct', type='numeric', format=percentage),
            dict(id='Actual (mi)', name='Actual Miles', type='numeric', format=fixed),
            dict(id='pbpFIPS', name='pbpFIPS'),
            # dict(id='OBJECTID', name='OBJECTID'),
            # dict(id='Primary', name='Primary'),
            dict(id='Zoom', name='Zoom')
        ]

        town_table_data = DataTable(
            style_header={'whiteSpace': 'normal', 'height': 'auto', 'fontWeight': 'bold', 'text-align': 'center'},
            columns=town_columns,
            data=df_cleaned_towns.to_dict('records'),
            # page_size=20,
            style_table={'overflowX': 'scroll'},
            id='town_table'
            )

        county_map = create_county_map_from_state_data(df_cleaned_towns, selected_state, selected_county,
                                                       state_geometry_json)

        return df.Town.unique(), cleaned_towns_json, town_table_data, county_map, county_map, \
            'WandrerQuest data for ' + selected_county + ' county', town_table_data

    else:
        print('...selected_state: ' + selected_state + ' not coded yet')
        return {}


def get_town_json_for_town(locations_field, location_id, county_json):
    print('\nfunction get_town_json_for_town')
    for feature in county_json['features']:
        # print(str(feature['properties']['OBJECTID']) + ': ' + feature['properties']['TOWN'])
        if int(feature['properties'][locations_field]) == location_id:
            return feature

    return county_json


@callback(
    Output(component_id='my_choropleth', component_property='figure', allow_duplicate=True),
    Input(component_id='town_dropdown', component_property='value'),
    State(component_id='state_dropdown', component_property='value'),
    State(component_id='county_dropdown', component_property='value'),
    State('summary_data', 'data'),
    State('state_geometry_json', 'data'),
    State('county_map_cache', 'data'),
    State('county_data', 'data'), prevent_initial_call=True)
def create_town_map(selected_town, selected_state, selected_county, summary_data, county_json, cached_county_map,
                    county_data):
    # TODO: Refactor this large callback into smaller chained ones that output just a single element. Each should be easier to make clientside.
    # TODO: Refactor this callback to save figure in a dcc.Store, then write a clientside callback to display it.
    # TODO: Trigger the clientside callback from the town dropdown and the dcc.Store used above. If town dropdown is blank return stored county map instead.
    print("\ncallback create_town_map")
    # print('---Triggered by: ' + ctx.triggered_id)
    if not selected_town:
        print('...returning from create_town_map early because town not chosen')
        return cached_county_map

    if not selected_county:
        print('...returning from create_town_map early because county not chosen')
        return cached_county_map

    print('...selected_state: ' + selected_state)
    print('...selected_county: ' + selected_county)
    print('...selected_town: ' + selected_town)

    df_county_data = pd.read_json(county_data, orient='split')
    df_town_data = df_county_data[df_county_data['Town'] == selected_town]
    # actual_pct_col = df_town_data['Actual Pct']

    # df = load_county_by_name(selected_state, selected_county, summary_data)
    df = load_town_boundaries(selected_state, selected_county, summary_data)
    # print('...df')
    # print(df)

    # filter by county and town.
    df_towns = df[(df['County'] == selected_county) & (df['Town'] == selected_town)]
    # print(df_towns)

    dff = df_StateWQData[
        (df_StateWQData['State'] == selected_state) & (df_StateWQData['CountyName'] == selected_county)]
    locations_field = dff.iloc[0]['GeoidPropertyName']

    if locations_field == 'pbpFIPS':
        oid = int(df_towns.pbpFIPS)
    else:
        oid = int(df_towns.OBJECTID)

    town_json = get_town_json_for_town(locations_field, oid, county_json)

    town_latitude, town_longitude = get_center_coords_from_town_json(town_json, oid, locations_field)

    # zoom = 9.5  # default zoom level for towns?
    town_zoom = float(df_town_data.Zoom)

    if town_latitude:
        print('...town_latitude: ' + str(town_latitude))

    if town_longitude:
        print('...town_longitude: ' + str(town_longitude))

    fig = px.choropleth_mapbox(df_town_data, geojson=town_json, locations=locations_field, color='Actual Pct',
                               color_continuous_scale=my_color_scale,
                               mapbox_style="carto-positron",
                               zoom=town_zoom,
                               center={"lat": town_latitude, "lon": town_longitude},
                               opacity=0.5,
                               range_color=[0, 1],
                               hover_data=['County', 'Town']
                               )
    fig = fig.update_layout(margin={"r": 1, "t": 1, "l": 1, "b": 1})
    return fig



if __name__ == "__main__":
    app.run_server(debug=True)
    # app.run_server(debug=False)
    # Host  0.0.0.0 makes app visible on my private wifi to all devices.
    # app.run_server(host="0.0.0.0", port="8050")
