import streamlit as st
import numpy as np
import os
import json
import pandas as pd
import geopandas as gpd

os.chdir("/Users/DarylTay/Documents/Github/bokeh-plots")

### 2000 - 2004

old_df = pd.read_csv('datasets/population-density/singapore-residents-by-planning-area-subzone-age-group-and-sex-june-2000-onwards.csv')

old_df = old_df[['planning_area','resident_count','year']]

# Exclude 2005 as 2005 data does not have some locations
result = old_df.groupby(['planning_area','year'],as_index = False)[['resident_count']].sum()
result = result.loc[~(result['year']==2005)]
result.columns = ['planning area','year','total']
result['planning area'] = result['planning area'].str.upper()
#result

### 2005 - 2010
df_shape = gpd.read_file('datasets/population-density/PLAN_BDY_AGE_GENDER_2005.shp')
df_shape.columns
df_shape = df_shape[['PLN_AREA_N','TOTAL']]
df_shape['year'] = [2005 for i in range(df_shape.shape[0])]

for year in range(2006,2011):
    df = gpd.read_file('datasets/population-density/PLAN_BDY_AGE_GENDER_' + str(year) + '.shp')[['PLN_AREA_N','TOTAL']]
    df['year'] = [year for i in range(df.shape[0])]
    #print(str(year) + str(df.shape))
    df_shape = pd.concat([df_shape,df])

df_shape.columns = ['planning area','total','year']
total = list(df_shape['total'])
df_shape = df_shape[['planning area','year']]
df_shape['total'] = total
#df_shape

### 2011 - 2019 
df2 = pd.read_csv('datasets/population-density/planning-area-subzone-age-group-sex-and-type-of-dwelling-june-2011-2019.csv')

result2 = df2.groupby(['planning_area','year',],as_index = False)[['resident_count']].sum()
result2.columns = ['planning area','year','total']
result2['planning area'] = result2['planning area'].str.upper()
#result2

## Concatenate all together
final_df = pd.concat([result,df_shape,result2])
#export = final_df.to_excel('population count 2000 - 2019.xlsx')

### importing of base map

map_year = ['98','08','14']

map_98 = gpd.read_file('datasets/population-density/maps/map_98_edited.geojson')
map_08 = gpd.read_file('datasets/population-density/maps/map_08_edited.geojson')
map_14 = gpd.read_file('datasets/population-density/maps/map_14_edited.geojson')
map_19 = gpd.read_file('datasets/population-density/maps/map_19.geojson')

df_98 = final_df.loc[final_df['year']==2000]
year_08=[2001,2002,2003,2004,2005,2006,2007,2008,2009,2010]
year_14=[2011,2012,2013,2014,2015,2016,2017,2018,2019]

df_08 = final_df.loc[final_df['year'].isin(year_08)]
df_14 = final_df.loc[final_df['year'].isin(year_14)]

map_df_98 = map_98.merge(df_98,left_on='planning_area',right_on='planning area',how='left')
map_df_08 = map_08.merge(df_08,left_on='planning_area',right_on='planning area',how='left')
map_df_14 = map_14.merge(df_14,left_on='planning_area',right_on='planning area',how='left')

map_df_overall = pd.concat([map_df_98,map_df_08])
map_df_overall = gpd.GeoDataFrame(pd.concat([map_df_overall,map_df_14]))
#map_df_overall.columns

map_df_overall= map_df_overall[['planning_area','geometry','year','total']]
#map_df_overall.to_file('overall_map_2000_2019.geojson',driver="GeoJSON")

map_df_overall_14 = map_df_overall.loc[map_df_overall['year'].isin(year_14)]
#map_df_overall_14.to_file('overall_map_2011_2019.geojson',driver="GeoJSON")

xs = []
ys = []
for obj in map_98.geometry.boundary:
    if obj.type == 'LineString':
        obj_x, obj_y = obj.xy
        xs.append([[list(obj_x)]])
        ys.append([[list(obj_y)]])
    elif obj.type == 'MultiLineString':
        obj_x = []
        obj_y = []
        for line in obj:
            line_x, line_y = line.xy
            obj_x.append([list(line_x)])
            obj_y.append([list(line_y)])
        xs.append(obj_x)
        ys.append(obj_y)

map_98_pa = map_98['planning_area'].values
map_98_sf = map_98['planning_area_sf'].values
map_98_df = pd.DataFrame({'planning_area':map_98_pa,'planning_area_sf':map_98_sf,'xs':xs,'ys':ys})

xs = []
ys = []
for obj in map_08.geometry.boundary:
    if obj.type == 'LineString':
        obj_x, obj_y = obj.xy
        xs.append([[list(obj_x)]])
        ys.append([[list(obj_y)]])
    elif obj.type == 'MultiLineString':
        obj_x = []
        obj_y = []
        for line in obj:
            line_x, line_y = line.xy
            obj_x.append([list(line_x)])
            obj_y.append([list(line_y)])
        xs.append(obj_x)
        ys.append(obj_y)

map_08_pa = map_08['planning_area'].values
map_08_sf = map_08['planning_area_sf'].values
map_08_df = pd.DataFrame({'planning_area':map_08_pa,'planning_area_sf':map_08_sf,'xs':xs,'ys':ys})

xs = []
ys = []
for obj in map_14.geometry.boundary:
    if obj.type == 'LineString':
        obj_x, obj_y = obj.xy
        xs.append([[list(obj_x)]])
        ys.append([[list(obj_y)]])
    elif obj.type == 'MultiLineString':
        obj_x = []
        obj_y = []
        for line in obj:
            line_x, line_y = line.xy
            obj_x.append([list(line_x)])
            obj_y.append([list(line_y)])
        xs.append(obj_x)
        ys.append(obj_y)

map_14_pa = map_14['planning_area'].values
map_14_sf = map_14['planning_area_sf'].values
map_14_df = pd.DataFrame({'planning_area':map_14_pa,'planning_area_sf':map_14_sf,'xs':xs,'ys':ys})

final_df_all = pd.DataFrame()

for year in range(2000,2020):
    df_temp = final_df.loc[final_df['year']==year]
    if year ==2000:
        plot_temp = map_98_df.merge(df_temp, left_on = 'planning_area', right_on = 'planning area')
    elif 2001 <= year <=2010:
        plot_temp = map_08_df.merge(df_temp, left_on = 'planning_area', right_on = 'planning area')
    elif year >=2011:
        plot_temp = map_14_df.merge(df_temp, left_on = 'planning_area', right_on = 'planning area')
    final_df_all = pd.concat([final_df_all,plot_temp])

#final_df_all.to_excel('pop density map df.xlsx')
from bokeh.io import output_notebook, show, curdoc
from bokeh.plotting import figure, output_file
from bokeh.models.widgets import Slider
from bokeh.models import ColumnDataSource,CDSView, BooleanFilter,LinearColorMapper, ColorBar, HoverTool, CustomJS
from bokeh.palettes import brewer
from bokeh.layouts import widgetbox, row, column

#Define function that returns json_data for year selected by user.
start_year = 2019

overall = ColumnDataSource(final_df_all)
filtered = ColumnDataSource(final_df_all.loc[final_df_all['year']==start_year])

#Define a sequential multi-hue color palette.
palette = brewer['YlGnBu'][6]

#Reverse color order so that dark blue is highest obesity.
palette = palette[::-1]

#Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors. Input nan_color.
color_mapper = LinearColorMapper(palette = palette, low = 0, high = 300000)

#Define custom tick labels for color bar.
tick_labels = {'1': '< 5,000', '2': '5,000 - < 10,000', '3':'10,000 - < 50,000', '4':'50,000 - < 100,000', '5':'100,000 - < 150,000', '6':'150,000 - < 200,000', '7':'200,000 - < 250,000','8':'250,000 - < 300,000'}

#Add hover tool
hover = HoverTool(tooltips = [ ('Region','@planning_area'),('Year','@year'),('Population Count', '@total')])

#Create color bar. 
color_bar = ColorBar(color_mapper=color_mapper, label_standoff=6,width = 500, height = 20,
                     border_line_color=None,location = (0,0), orientation = 'horizontal', major_label_overrides = tick_labels)
#Create figure object.
p = figure(plot_height = 500 , plot_width = 700, toolbar_location = None,tools = [hover])
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.xaxis.visible = False
p.yaxis.visible = False

#Add patch renderer to figure. 
#p.patches('xs','ys', source = plot_geosource,fill_color = {'field' :'total', 'transform' : color_mapper},line_color = 'black', line_width = 0.25, fill_alpha = 1)
p.multi_polygons(xs='xs', ys='ys', line_color='black',fill_color={'field' :'total', 'transform' : color_mapper},fill_alpha=1, line_width = 0.25,source=filtered)

#Specify layout
p.add_layout(color_bar, 'below')

slider = Slider(title = 'Year',start = 2000, end = 2019, step = 1, value = start_year)

callback = CustomJS(args=dict(source=overall, source2=filtered,slider=slider), code="""       
        const f = slider.value;
        source2.data['total']=[];
        source2.data['planning_area']=[];
        source2.data['planning_area_sf']=[];
        source2.data['xs']=[];
        source2.data['ys']=[];
        
        for (var i = 0; i <= source.data['planning_area'].length; i++){
          if (source.data['year'][i] == f){
            source2.data['xs'].push(source.data['xs'][i])
            source2.data['ys'].push(source.data['ys'][i])
            source2.data['planning_area_sf'].push(source.data['planning_area_sf'][i])
            source2.data['planning_area'].push(source.data['planning_area'][i])
            source2.data['total'].push(source.data['total'][i])
          }
        }
        source2.change.emit();
    """)

# Make a slider
slider.js_on_change('value', callback)

# Make a column layout of widgetbox(slider) and plot, and add it to the current document
layout = column(slider,p)
#curdoc().add_root(layout)
#output_file("Population Density of SG 2000 - 2019.html",mode='inline',root_dir=None)
#Display the plot
#show(layout)

st.title('Singapore Population Density in each Planning area from 2000 - 2019')

st.bokeh_chart(layout, use_container_width=False)