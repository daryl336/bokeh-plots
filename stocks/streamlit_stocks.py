import streamlit as st
from google.oauth2.service_account import Credentials
import gspread as gs
import os
import pandas as pd
import bokeh
import numpy as np
from bokeh.layouts import gridplot
from bokeh.plotting import figure, show
from bokeh.models import HoverTool, CustomJS, ColumnDataSource, DateRangeSlider, Dropdown, Select
from bokeh.layouts import widgetbox, row, column
from bokeh.io import output_file, show

# Create a connection object.
scopes = ['https://www.googleapis.com/auth/spreadsheets']

credentials = st.secrets["gcp_service_account"]

gc = gs.service_account_from_dict(credentials,scopes=scopes)

gsheet_url = st.secrets["private_gsheets_url"]
# Load Data on the Google Sheet.
# Uses st.cache to only rerun when the query changes or after 10 min.
#@st.cache(ttl=600)
def load_data(sheet_name):
    sh = gc.open_by_url(gsheet_url)
    stocks  = sh.worksheet(sheet_name)
    records = stocks.get_all_values()
    df = pd.DataFrame(records[1:],columns=records[0])
    return df

df = load_data('Record')
stock_name = load_data('Stock Codes')

do_not_use = ['EC WORLD REIT','SIA','CAPITACOM TRUST','SBJUN19 GX19060S','TEMASEKBOND']
names = [x for x in list(stock_name['Name'].unique()) if x not in do_not_use]

df = df.merge(stock_name,how='left',on='Symbol')

df['datetime_str'] = df['Date'] + ' ' + df['Time']
df['datetime'] = pd.to_datetime(df['datetime_str'],format='%d/%m/%Y %H:%M')
df['Date_in_dateformat'] = pd.to_datetime(df['Date'],format='%d/%m/%Y')
df['date_string'] = df['Date_in_dateformat'].apply(lambda x: str(x)[:10])

ES3 = df[df['Symbol']=='ES3']

start_date = pd.to_datetime(df['Date_in_dateformat'].iloc[0],format='%d/%m/%Y')
end_date = pd.to_datetime(df['Date_in_dateformat'].iloc[df.shape[0]-1],format='%d/%m/%Y')

source = ColumnDataSource(df)
filtered = ColumnDataSource(ES3)

# Select list
select = Select(title="Stocks:", value=names[0], options=names)

#Add hover tool
hover = HoverTool(tooltips = [('Date','@datetime{%F %H:00}'),('Stock Name','@Name'),('Price','$@Price')],formatters = {'@datetime' : 'datetime'},mode='vline')

# Make a slider
date_range_slider = DateRangeSlider(value=(start_date, end_date),start=start_date, end=end_date)

p1 = figure(x_axis_type="datetime", title="Stock Prices", tools = [hover])
p1.grid.grid_line_alpha=0.3
p1.xaxis.axis_label = 'Date'
p1.yaxis.axis_label = 'Price'

p1.line('datetime', 'Price', color='#A6CEE3', source=filtered, line_width=2, line_color='#3288bd')
p1.legend.location = "top_left"

callback = CustomJS(args=dict(source=source, source2=filtered,slider=date_range_slider,select=select), code="""       
        function formatDate(date) {
            var d = new Date(date),
                month = '' + (d.getMonth() + 1),
                day = '' + d.getDate(),
                year = d.getFullYear();

            if (month.length < 2) 
                month = '0' + month;
            if (day.length < 2) 
                day = '0' + day;

            return [year, month, day].join('-');
        }
        const name = select.value
        console.log(name)

        const f = new Date(slider.value[0])
        const start_date = formatDate(f)

        const g = new Date(slider.value[1])
        const end_date = formatDate(g)

        console.log(start_date)
        console.log(end_date)
        source2.data['datetime']=[];
        source2.data['Price']=[];

        for (var i = 0; i <= source.data['datetime'].length; i++){
          if (source.data['date_string'][i] <= end_date && source.data['date_string'][i] >= start_date){
              if (source.data['Name'][i] == name){
                source2.data['datetime'].push(source.data['datetime'][i])
                source2.data['Price'].push(source.data['Price'][i])
              }
          }
        }
        source2.change.emit();
    """)


date_range_slider.js_on_change('value', callback)
select.js_on_change('value',callback)
layout = row(column(p1,date_range_slider),select)

#show(layout)

st.title('Stocks!')

st.bokeh_chart(layout, use_container_width=False)