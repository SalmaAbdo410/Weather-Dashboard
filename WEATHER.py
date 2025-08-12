import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

# --- Load Data ---
@st.cache_data
def load_data():
    df = pd.read_csv("Cairo-Weather-clean (1).csv")
    df = df.dropna(axis=1, how='all')
    
    # Convert date columns
    df['time'] = pd.to_datetime(df['time'])
    if 'sunrise_iso8601' in df.columns:
        df['sunrise_iso8601'] = pd.to_datetime(df['sunrise_iso8601'])
    if 'sunset_iso8601' in df.columns:
        df['sunset_iso8601'] = pd.to_datetime(df['sunset_iso8601'])
    
    # Extract time features
    df['month'] = df['time'].dt.month
    df['year'] = df['time'].dt.year
    df['day_of_week'] = df['time'].dt.dayofweek
    df['date'] = df['time'].dt.date
    
    # Add seasons
    def get_season(month):
        if month in [12, 1, 2]: return 'Winter'
        elif month in [3, 4, 5]: return 'Spring'
        elif month in [6, 7, 8]: return 'Summer'
        else: return 'Autumn'
    df['season'] = df['month'].apply(get_season)
    
    return df

df = load_data()

# --- Page Config ---
st.set_page_config(page_title="🌦️ Cairo Weather Dashboard", layout="wide")
st.title("🌦️ Cairo Weather Dashboard")
st.markdown("""
Welcome to the **Cairo Weather Dashboard**!  
Explore historical weather trends for Cairo, Egypt.  
*Data last updated: {}*
""".format(df['time'].max().strftime('%Y-%m-%d')))

# --- Sidebar ---
st.sidebar.title("Cairo Weather Dashboard")
st.sidebar.header("Filter Options")
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=[df['time'].min(), df['time'].max()],
    min_value=df['time'].min(),
    max_value=df['time'].max()
)

selected_metric = st.sidebar.selectbox(
    "Select Weather Metric",
    options=[
        'temperature_2m_mean_°C',
        'relative_humidity_2m_mean_%',
        'wind_speed_10m_mean_km/h',
        'rain_sum_mm'
    ],
    index=0
)

# Filter Data
if len(date_range) == 2:
    df_filtered = df[(df['date'] >= date_range[0]) & (df['date'] <= date_range[1])]
else:
    df_filtered = df.copy()

# --- Key Metrics ---
st.subheader("📊 Key Weather Metrics")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Avg Temperature", f"{df_filtered['temperature_2m_mean_°C'].mean():.1f}°C")
with col2:
    st.metric("Max Temperature", f"{df_filtered['temperature_2m_mean_°C'].max():.1f}°C")
with col3:
    st.metric("Avg Humidity", f"{df_filtered['relative_humidity_2m_mean_%'].mean():.1f}%")
with col4:
    st.metric("Total Rainfall", f"{df_filtered['rain_sum_mm'].sum():.1f} mm")

# --- Recent Forecast ---
st.subheader("📅 Recent Weather Conditions")
st.dataframe(
    df_filtered[['time', 'temperature_2m_mean_°C', 'relative_humidity_2m_mean_%', 
                'wind_speed_10m_mean_km/h', 'rain_sum_mm']].tail(5).sort_index(ascending=False),
    column_config={
        "time": "Date",
        "temperature_2m_mean_°C": "Temp (°C)",
        "relative_humidity_2m_mean_%": "Humidity (%)",
        "wind_speed_10m_mean_km/h": "Wind (km/h)",
        "rain_sum_mm": "Rain (mm)"
    },
    hide_index=True
)

# --- Charts Section ---
st.subheader("📈 Weather Trends Analysis")

# Row 1: Season Distribution and Monthly Averages
col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Season Distribution")
    season_counts = df_filtered['season'].value_counts().reset_index()
    fig_pie = px.pie(
        season_counts,
        names='season',
        values='count',
        color_discrete_sequence=px.colors.sequential.Aggrnyl,
        hole=0.4
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    st.markdown(f"#### Monthly {selected_metric.replace('_', ' ').title()}")
    monthly_avg = df_filtered.groupby('month')[selected_metric].mean().reset_index()
    fig_bar = px.bar(
        monthly_avg,
        x='month',
        y=selected_metric,
        text=selected_metric,
        color=selected_metric,
        color_continuous_scale=px.colors.sequential.Sunset
    )
    fig_bar.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    fig_bar.update_layout(yaxis=dict(visible=False))
    st.plotly_chart(fig_bar, use_container_width=True)

# Row 2: Time Series
st.markdown(f"#### {selected_metric.replace('_', ' ').title()} Over Time")
fig_line = px.line(
    df_filtered,
    x='time',
    y=selected_metric,
    markers=True,
    color_discrete_sequence=px.colors.qualitative.Set1
)
st.plotly_chart(fig_line, use_container_width=True)


# --- Additional Charts Section ---
st.subheader("📊 Extra Weather Insights")

# 1️⃣ Average Humidity in Wet vs Dry Months
st.markdown("#### Average Humidity in Wet vs Dry Months")
monthly_rain = df_filtered.groupby('month')['rain_sum_mm'].sum()
wet_months = monthly_rain[monthly_rain > monthly_rain.mean()].index
df_filtered['MonthType'] = df_filtered['month'].apply(lambda x: 'Wet' if x in wet_months else 'Dry')

humidity_avg = df_filtered.groupby('MonthType')['relative_humidity_2m_mean_%'].mean().reset_index()
fig_humidity = px.bar(
    humidity_avg,
    x='MonthType',
    y='relative_humidity_2m_mean_%',
    color='MonthType',
    color_discrete_sequence=px.colors.sequential.Aggrnyl
)
st.plotly_chart(fig_humidity, use_container_width=True)


# 3️⃣ Monthly Rainfall Trend
st.markdown("#### Monthly Rainfall Trend")
monthly_rainfall = df_filtered.groupby('month')['rain_sum_mm'].sum().reset_index()
fig_rain = px.line(
    monthly_rainfall,
    x='month',
    y='rain_sum_mm',
    markers=True,
    color_discrete_sequence=px.colors.qualitative.Set1
)
st.plotly_chart(fig_rain, use_container_width=True)

# --- 6. Seasons vs Wind Speed ---
st.subheader("Seasons vs Wind Speed")
fig6 = px.violin(df, x='season', y='wind_speed_10m_mean_km/h',
                 color='season',
                 box=True,
                 color_discrete_sequence=px.colors.qualitative.Set1)
st.plotly_chart(fig6, use_container_width=True)


# --- Bar Chart: Average Wind Speed vs Temperature by Season ---
st.subheader(" Average Wind Speed vs Temperature")
fig_bar = px.bar(
    df,
    x='season',
    y='wind_speed_10m_mean_km/h',
    color='temperature_2m_mean_°C',
    barmode='group',
    color_continuous_scale='Viridis'
)
st.plotly_chart(fig_bar, use_container_width=True)


# ---  Cairo Temperature  ---

st.subheader("🌡️ Temperature Patterns by Time of Day")

# Create time features for heatmap
df_filtered['hour'] = df_filtered['time'].dt.hour
df_filtered['day_of_week'] = df_filtered['time'].dt.day_name()
df_filtered['month_name'] = df_filtered['time'].dt.month_name()

# Create tabs for different temporal views
tab1, tab2 = st.tabs(["By Hour of Day", "By Day of Week"])

with tab1:
    # Hourly heatmap
    heatmap_data = df_filtered.pivot_table(
        index='hour',
        columns='day_of_week',
        values='temperature_2m_mean_°C',
        aggfunc='mean'
    )
    
    # Reorder columns to start with Monday
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data[days_order]
    
    fig = px.imshow(
        heatmap_data,
        labels=dict(x="Day of Week", y="Hour of Day", color="Temperature (°C)"),
        color_continuous_scale="thermal",
        title="Average Temperature by Hour and Day"
    )
    fig.update_xaxes(side="top")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    # Daily heatmap
    heatmap_data = df_filtered.pivot_table(
        index='day_of_week',
        columns='month_name',
        values='temperature_2m_mean_°C',
        aggfunc='mean'
    )
    
    # Reorder for logical display
    months_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                   'July', 'August', 'September', 'October', 'November', 'December']
    heatmap_data = heatmap_data[months_order]
    
    fig = px.imshow(
        heatmap_data,
        labels=dict(x="Month", y="Day of Week", color="Temperature (°C)"),
        color_continuous_scale="thermal",
        title="Average Temperature by Day and Month"
    )
    fig.update_xaxes(side="top")
    st.plotly_chart(fig, use_container_width=True)



# Add interpretation guide
st.markdown("""
**How to read these heatmaps:**
- 🔥 Warmer temperatures shown in yellow/Orange
- ❄️ Cooler temperatures shown in blue/purple
""")
