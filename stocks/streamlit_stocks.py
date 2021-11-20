import streamlit as st
import gspread as gs
import pandas as pd
from bokeh.layouts import gridplot
from bokeh.plotting import figure, show
from bokeh.models import HoverTool, CustomJS, ColumnDataSource, DateRangeSlider, Dropdown, Select, DataTable, TableColumn
from bokeh.layouts import widgetbox, row, column
from bokeh.io import output_file, show
from bokeh.io import curdoc
from math import pi

#Bokeh theme
curdoc().theme = 'dark_minimal'

# Create a connection object.
scopes = ['https://www.googleapis.com/auth/spreadsheets']

credentials = st.secrets["gcp_service_account"]

gc = gs.service_account_from_dict(credentials,scopes=scopes)

hourly_record_url = st.secrets["stocks_hourly_record_url"]
daily_record_url = st.secrets["daily_data"]

# Load Data on the Google Sheet.
# Uses st.cache to only rerun when the query changes or after 10 min.
#@st.cache(ttl=600)
def load_data(gsheet_url,sheet_name):
    sh = gc.open_by_url(gsheet_url)
    stocks  = sh.worksheet(sheet_name)
    records = stocks.get_all_values()
    df = pd.DataFrame(records[1:],columns=records[0])
    return df

past_data = load_data(hourly_record_url,'past data')
df = load_data(hourly_record_url,'Record')
df = pd.concat([past_data,df])

# Load stock names
stock_name = load_data(hourly_record_url,'Stock Codes')

# Generate stock names list
do_not_use = ['EC WORLD REIT','SIA','CAPITACOM TRUST','SBJUN19 GX19060S','TEMASEKBOND','STI ETF']
names = [x for x in list(stock_name['Name'].unique()) if x not in do_not_use]

# Merge with the main dataset
df = df.merge(stock_name,how='left',on='Symbol')

df['date_string'] = df['Date'].apply(lambda x: str(x).strip())
# Manipulation
df['datetime_str'] = df['Date'] + ' ' + df['Time']
df['datetime'] = pd.to_datetime(df['datetime_str'],format='%Y-%m-%d %H:%M')

ES3 = df[df['Symbol']=='ES3']

sti_source = ColumnDataSource(ES3)
sti_filtered = ColumnDataSource(ES3.copy())

sti_start_date = pd.to_datetime(ES3['date_string'].iloc[0],format='%Y-%m-%d')
sti_end_date = pd.to_datetime(ES3['date_string'].iloc[ES3.shape[0]-1],format='%Y-%m-%d')

## Plotting of STI ETF first
hover = HoverTool(tooltips = [('Date','@datetime{%F %H:00}'),('Price','$@Price')],formatters = {'@datetime' : 'datetime'},mode='vline')
sti_date_range_slider = DateRangeSlider(value=(sti_start_date, sti_end_date),start=sti_start_date, end=sti_end_date)

sti_plot = figure(x_axis_type="datetime", title="STI", tools = [hover])
sti_plot.grid.grid_line_alpha=0.3
sti_plot.xaxis.axis_label = 'Date'
sti_plot.yaxis.axis_label = 'Price'

sti_plot.line('datetime', 'Price', color='#A6CEE3', source=sti_filtered, line_width=2, line_color='#3288bd',legend_label='STI')
sti_plot.legend.location = "top_left"

sti_callback = CustomJS(args=dict(source=sti_source, source2=sti_filtered,slider=sti_date_range_slider), code="""       
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
            source2.data['datetime'].push(source.data['datetime'][i])
            source2.data['Price'].push(source.data['Price'][i])
          }
        }
        source2.change.emit();
    """)


sti_date_range_slider.js_on_change('value', sti_callback)
sti_layout = column(sti_plot,sti_date_range_slider)
#show(sti_layout)

## Main Interactive Plots with all other stocks
D05 = df[df['Symbol']=='D05']

start_date = pd.to_datetime(df['date_string'].iloc[0],format='%Y-%m-%d')
end_date = pd.to_datetime(df['date_string'].iloc[df.shape[0]-1],format='%Y-%m-%d')

source = ColumnDataSource(df)
filtered = ColumnDataSource(D05)

# Select list
select = Select(title="Stocks:", value=names[0], options=names)

#Add hover tool
hover = HoverTool(tooltips = [('Date','@datetime{%F %H:00}'),('Price','$@Price')],formatters = {'@datetime' : 'datetime'},mode='vline')

# Make a slider
date_range_slider = DateRangeSlider(value=(start_date, end_date),start=start_date, end=end_date)

p1 = figure(x_axis_type="datetime", title="Stock Prices", tools = [hover])
p1.grid.grid_line_alpha=0.3
p1.xaxis.axis_label = 'Date'
p1.yaxis.axis_label = 'Price'

p1.line('datetime', 'Price', color='#A6CEE3', source=filtered, line_width=2, line_color='#3288bd')

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

# Generate statistics summary
def generateMaxMinDetails(df):
    max_df = df.groupby('Symbol')[['Price']].max().reset_index()
    min_df = df.groupby('Symbol')[['Price']].min().reset_index()
    unique_symbol = list(df['Symbol'].unique())
    result = []
    for i in unique_symbol:
        max_value = max_df[max_df['Symbol']==i].iloc[0][1]
        max_temp = df[ (df['Price']==max_value) & (df['Symbol']==i) ]
        max_details = list(max_temp[['Symbol','Name','datetime_str','Price']].iloc[max_temp.shape[0]-1]) + ['All Time High']

        min_value = min_df[min_df['Symbol']==i].iloc[0][1]
        min_temp = df[ (df['Price']==min_value) & (df['Symbol']==i) ]
        min_details = list(min_temp[['Symbol','Name','datetime_str','Price']].iloc[min_temp.shape[0]-1]) + ['All Time Low']

        result.append(max_details)
        result.append(min_details)
    return pd.DataFrame(result,columns=['Symbol','Name','datetime_str','Price','status'])

minmax = generateMaxMinDetails(df)

columns = [
    TableColumn(field='Name', title='Name'),
    TableColumn(field='Symbol', title='Symbol'),
    TableColumn(field='datetime_str', title='DateTime'),
    TableColumn(field='Price', title='Price')
    ]

interactive_layout = column(row(select,p1),date_range_slider)
#show(interactive_layout)

### Technical Analysis Charts
# Generate stock symbols

symbols = ['D05','O39','U11','Z74','M44U','N2IU','RW0U','A17U','C38U','AU8U','CY6U','AJBU']
daily_df = []
for code in symbols:
    temp = load_data(daily_record_url,code)
    temp['Symbol'] = [code] * temp.shape[0]
    daily_df.append(temp)

daily_df = pd.concat(daily_df)
daily_df= daily_df[daily_df['Date']>='2019-11-19']
daily_df['datetime'] = pd.to_datetime(daily_df['Date'],format='%Y-%m-%d')

# Merge with the main dataset
daily_df = daily_df.merge(stock_name,how='left',on='Symbol')
## Label the changes for colouring
# if True then it is green. False will be red.
def changes(row):
    if row.Close > row.Open:
        return True
    else:
        return False

daily_df['changes'] = daily_df.apply(lambda x: changes(x),axis=1)

w = 12*60*60*1000 # half day in ms

daily_D05 = daily_df[daily_df['Symbol']=='D05'][['datetime','High','Low']]
daily_increased = daily_df[ (daily_df['changes']==True) & (daily_df['Symbol']=='D05') ][['datetime','Open','Close']]
daily_decreased = daily_df[ (daily_df['changes']==False) & (daily_df['Symbol']=='D05') ][['datetime','Open','Close']]
ema_daily = daily_df[daily_df['Symbol']=='D05'][['datetime','ema12','ema26']]
sma_daily = daily_df[daily_df['Symbol']=='D05'][['datetime','sma20']]

ema_source = ColumnDataSource(daily_df)
ema_filtered = ColumnDataSource(daily_D05)
ema_increased = ColumnDataSource(daily_increased)
ema_decreased = ColumnDataSource(daily_decreased)
ema_data = ColumnDataSource(ema_daily)
sma_data = ColumnDataSource(sma_daily)

TOOLS = "pan,wheel_zoom,box_zoom,reset,save"

p = figure(x_axis_type="datetime", tools=TOOLS, plot_width=1000, title = "Candlestick")
p.xaxis.major_label_orientation = pi/4
p.grid.grid_line_alpha=0.3

p.segment('datetime', 'High', 'datetime', 'Low', color="white",source=ema_filtered)
p.vbar('datetime', w, 'Open', 'Close', fill_color="#04AC07", line_color="black",source=ema_increased)
p.vbar('datetime', w, 'Open', 'Close', fill_color="#F2583E", line_color="black",source=ema_decreased)
p.line('datetime', 'ema12', color='#A6CEE3', source=ema_data, line_width=2, line_color='#18a7e7',legend_label='EMA12')
p.line('datetime', 'ema26', color='#A6CEE3', source=ema_data, line_width=2, line_color='#efa30f',legend_label='EMA26')
p.line('datetime', 'sma20', color='#A6CEE3', source=sma_data, line_width=2, line_color='#c90076',legend_label='SMA20')
p.legend.location = "top_left"

ema_callback = CustomJS(args=dict(source=ema_source, source2=ema_filtered,source_increased=ema_increased,source_decreased=ema_decreased,ema_data=ema_data,sma_data=sma_data,slider=date_range_slider,select=select), code="""       
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
        source2.data['High']=[];
        source2.data['Low']=[];

        source2.data['datetime']=[];
        source2.data['High']=[];
        source2.data['Low']=[];

        source_increased.data['datetime']=[];
        source_increased.data['Open']=[];
        source_increased.data['Close']=[];
        
        source_decreased.data['datetime']=[];
        source_decreased.data['Open']=[];
        source_decreased.data['Close']=[];

        ema_data.data['datetime']=[];
        ema_data.data['ema12']=[];
        ema_data.data['ema26']=[];

        sma_data.data['datetime']=[];
        sma_data.data['sma20']=[];

        for (var i = 0; i <= source.data['datetime'].length; i++){
          if (source.data['Date'][i] <= end_date && source.data['Date'][i] >= start_date){
              if (source.data['Name'][i] == name){
                  source2.data['datetime'].push(source.data['datetime'][i])
                  source2.data['High'].push(source.data['High'][i])
                  source2.data['Low'].push(source.data['Low'][i])

                  ema_data.data['datetime'].push(source.data['datetime'][i])
                  ema_data.data['ema12'].push(source.data['ema12'][i])
                  ema_data.data['ema26'].push(source.data['ema26'][i])

                  sma_data.data['datetime'].push(source.data['datetime'][i])
                  sma_data.data['sma20'].push(source.data['sma20'][i])

                if (source.data['changes'][i] == true){
                    source_increased.data['datetime'].push(source.data['datetime'][i])
                    source_increased.data['Open'].push(source.data['Open'][i])
                    source_increased.data['Close'].push(source.data['Close'][i])
                }
                if (source.data['changes'][i] == false){
                    source_decreased.data['datetime'].push(source.data['datetime'][i])
                    source_decreased.data['Open'].push(source.data['Open'][i])
                    source_decreased.data['Close'].push(source.data['Close'][i])
                }
              }
          }
        }
        source2.change.emit();
        source_increased.change.emit();
        source_decreased.change.emit();
        ema_data.change.emit();
        sma_data.change.emit();
    """)

date_range_slider.js_on_change('value', ema_callback)
select.js_on_change('value',ema_callback)

ema_layout = column(p)
#show(ema_layout)

# Layout of all the charts
main_layout = column(sti_layout,interactive_layout,ema_layout)
show(main_layout)

# Initiate streamlit
st.title('Stocks Dashboard')
#st.write('All Time High and Low Since 19 Nov 2019')
#st.dataframe(data=minmax)
st.write('Stocks!')
st.bokeh_chart(main_layout, use_container_width=True)
st.write('Technical Analysis!')