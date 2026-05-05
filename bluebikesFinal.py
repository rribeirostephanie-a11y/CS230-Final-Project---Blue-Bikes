"""
Name: Stephanie Ribeiro 
CS230: Section 5
Data: blue bikes boston trips in 2020
URL: Link to your web application on Streamlit Cloud (if posted)
Description: 
This program ... (a few sentences about your program and the queries and charts)
.
References:
(and links to any websites or external tutorials you may have used)
"""
import streamlit as st 
import pandas as pd
import matplotlib.pyplot as plt 
import pydeck as pdk
import zipfile


#ths is going to give back the toal trips nad average duration  - return two functions
ZIP_FILE = "202009-bluebikes-tripdata(in).csv.zip"
DATA_FILE = "202009-bluebikes-tripdata(in).csv"

@st.cache_data
def load_clean_data(zip_file, data_file, max_rows=None):
    with zipfile.ZipFile(zip_file, "r") as zip_ref:
        file_list = zip_ref.namelist()
        csv_path = [file for file in file_list if file.endswith(data_file)][0]

        with zip_ref.open(csv_path) as file:
            df = pd.read_csv(file, nrows=max_rows)

    df["trip_minutes"] = df["tripduration"] / 60
    df["starttime"] = pd.to_datetime(df["starttime"], errors="coerce", format="mixed")
    df = df.dropna(subset=["starttime"])
    df["hour"] = df["starttime"].dt.hour

    totalTrips = len(df)
    averageDuration = round(df["trip_minutes"].mean(), 2)

    return df, totalTrips, averageDuration

def get_top_counts(df, column_name, top_num=10):
    return df[column_name].value_counts().head(top_num)
#counts ho much each value appears in the column then will keep the top results

def main():
    st.set_page_config(page_title ="Blue Bikes Boston Explorer", layout="wide") #revist this

    #bulds the sidebar
    st.sidebar.title("Blue Bikes Filters")

    st.title("Blue Bike Boston Trip Explorer")

    st.write("this app explores how people have used bikes in Boston."
             "Use the filters to explore riding pattersn, busy stations, and destinations."
    )
    
    df, totalTrips, averageDuration = load_clean_data(ZIP_FILE, DATA_FILE)

    #get the rider types and try ot make it look cleaner
    userTypes = sorted(df["usertype"].dropna().unique()) #removes blanks 

    #add a list comp here
    user_type_options = [user for user in userTypes]

    #dropdown for the interactive featuer where user can sselect + filter the data
    selected_user_type = st.sidebar.selectbox("Choose a rider type:", user_type_options)
   
    #*******FIX********
    filters_df = df[df["usertype"] == selected_user_type]

    column1, column2, column3 = st.columns(3)

    #show the numner of trips for the rider type, the average trip lemngeth in min, and the most common station used 
    column1.metric("Total Trips", f"{len(filters_df):,}") 
    column2.metric("Average Trip Length", f"{round(filters_df['trip_minutes'].mean(), 2)} minutes")
    column3.metric("Most Popular Start Station", filters_df["start station name"].mode()[0])
    st.divider()

    st.header ("1. What time of day are blue bikes used the most?")

    tripsPerHour = pd.pivot_table(
        filters_df,
        values="bikeid",
        index="hour",
        aggfunc="count" 
    ).rename(columns={"bikeid":"Number of Trips"})

    #make the peak hour red 
    peak_hour = tripsPerHour["Number of Trips"].idxmax() 
    colors = ["red" if hour == peak_hour else "blue" for hour in tripsPerHour.index]     

    fig, ax = plt.subplots(figsize=(12,5))
    ax.bar(tripsPerHour.index, tripsPerHour["Number of Trips"], color=colors)

    ax.set_title(f"Trips by Hour for {selected_user_type}s")
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Number of Trips")
    ax.set_xticks(range(0,24))
    ax.set_xticklabels(range(0,24), fontsize=9)

    ax.legend(
        handles=[
            plt.Rectangle((0,0),1,1, color="red", label=f"Busiest Hour ({peak_hour}:00)"),
            plt.Rectangle((0,0),1,1, color="blue", label="Other Hours")
        ]
    )

    st.pyplot(fig)

    st.write(
        "This chart shows the busiest riding hours. So the bars that are high mean that more people are starting trips during that time."
    )
    st.divider()

    #query number 2 
    st.header("2. Which blue bikes stations are the busiest, and where are they located?")
    st.write ("Explain what this sections does here")

    top_number = st.slider("Choose how many top stations to show:", 5,25,10)
    top_stations = get_top_counts(filters_df,"start station name", top_number)
    top_stations = top_stations.sort_values(ascending =True) 

    fig2,ax2 = plt.subplots()
    ax2.barh(top_stations.index,top_stations.values)
    ax2.set_title(f"Top{top_number} Busiest Start Stations")
    ax2.set_xlabel("Number of Trips")
    ax2.set_ylabel("Station Name")
    st.pyplot(fig2)

    st.subheader("Map of Busiest Stations")

    map_station = filters_df.groupby(
        ["start station name", "start station latitude", "start station longitude"]
    ).size().reset_index(name="trip_count")

    map_station = map_station.sort_values("trip_count", ascending=False).head(top_number)
    
    
    # Rename columns so PyDeck can read them more easily
    map_station = map_station.rename(columns={
        "start station name": "station",
        "start station latitude": "lat",
        "start station longitude": "lon"
    })

    # Make busier stations show as larger circles
    map_station["radius"] = map_station["trip_count"] / 2

    st.write("Hover over each map to view the Station and Amount of Trips at each staation:")
    
    
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_station,
        get_position="[lon, lat]",
        get_radius="radius",
        radius_min_pixels = 8,
        radius_max_pixels = 60,
        get_color=[0, 102, 204, 180],
        pickable=True,
    )

    view_state = pdk.ViewState(
        latitude=42.36,
        longitude=-71.08,
        zoom=11,
        pitch=0,
    )

    map = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "{station}\nTrips: {trip_count}"}
    )

    st.pydeck_chart(map)

    #query number 3
    st.divider()
    st.header("3. Where do trips from one station ususally end?")
    
    station_list = sorted(filters_df["start station name"].dropna().unique())
    selected_station = st.selectbox("Choose a starting station:", station_list)

    station_df = df[
        (df["start station name"] == selected_station) & 
        (df["usertype"] == selected_user_type)
    ]

    top_destinations = get_top_counts(station_df,"end station name",10)

    st.subheader(f"Top destinations from {selected_station}")

    st.dataframe(
        top_destinations.reset_index().rename(
            columns={
                "index": "End Station",
                "end station name": "Name of Station"
            }
        )
    )

    if len(top_destinations)>0:
        busiest_destination = top_destinations.idxmax()
        st.write(
            f"The most common destination from {selected_station} is {busiest_destination}"
        )



main()
