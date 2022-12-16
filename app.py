import json
import time
import streamlit as st
import requests
import pandas as pd
import datetime as dt
from io import StringIO

# set page config
st.set_page_config(page_title="LearnApp", page_icon="favicon.png")

# hide streamlit branding and hamburger menu
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.write("")
with col2:
    st.image("logo.png", width=225)
    st.write("")
with col3:
    st.write("")

st.write("----")

st.markdown(
    "<h2 style='text-align: center; color: white;'>Module Completion Calculator</h2>",
    unsafe_allow_html=True,
)
st.write("----")

# Kraken Auth Token
# functions for getting user specific course progress
url = "https://e3d72bp6aa.execute-api.ap-south-1.amazonaws.com/"
payload = {}
headers = {}
response = requests.request("GET", url, headers=headers, data=payload)
access_token = response.text

token = "Bearer " + access_token

# Function to get the data of all the courses, classes, workshops and advanced courses on LearnApp
@st.cache()
def get_learnapp_content():

    url = "https://catalog.prod.learnapp.com/catalog/discover"

    payload = {}
    headers = {"authorization": token, "x-api-key": "ZmtFWfKS9aXK3NZQ2dY8Fbd6KqjF8PDu"}

    response = requests.request("GET", url, headers=headers, data=payload)

    data = json.loads(response.text)

    courses_data = []
    for i in range(len(data["courses"])):
        for j in range(len(data["courses"][i]["items"])):
            courses_data.append(data["courses"][i]["items"][j])

    classes_data = []
    for i in range(len(data["webinars"])):
        for j in range(len(data["webinars"][i]["items"])):
            classes_data.append(data["webinars"][i]["items"][j])

    workshops_data = []
    for i in range(len(data["workshops"])):
        for j in range(len(data["workshops"][i]["items"])):
            workshops_data.append(data["workshops"][i]["items"][j])

    advcourses_data = []
    for i in range(len(data["advCourses"])):
        for j in range(len(data["advCourses"][i]["items"])):
            advcourses_data.append(data["advCourses"][i]["items"][j])

    learnapp_data = []

    for i in courses_data:
        learnapp_data.append(i)

    for i in classes_data:
        learnapp_data.append(i)

    for i in workshops_data:
        learnapp_data.append(i)

    for i in advcourses_data:
        learnapp_data.append(i)

    final_data = {}

    for i in learnapp_data:

        title = i["title"]
        contentType = i["contentType"]
        canonicalTitle = i["canonicalTitle"]
        id = i["id"]
        totalPlaybackTime = i["totalPlaybackTime"]
        try:
            assetUrl = (
                f"https://assets.learnapp.com/{i['assets']['card-238x165-jpg']['url']}"
            )
        except:
            assetUrl = "https://la-course-recommendation-engine.s3.ap-south-1.amazonaws.com/Basics+of+Trading.jpeg"

        field_data = {
            canonicalTitle: {
                "title": title,
                "canonicalTitle": canonicalTitle,
                "id": id,
                "totalPlaybackTime": totalPlaybackTime,
                "assetUrl": assetUrl,
                "contentType": contentType,
            }
        }

        final_data.update(field_data)

    return final_data


# Function to fetch the user_id of any user on LearnApp
def fetch_userid(email):
    email = email.replace("@", "%40")
    url = "https://hydra.prod.learnapp.com/kraken/users/search?q=" + email

    payload = {}
    headers = {
        "authorization": token,
        "x-api-key": "u36jbrsUjD8v5hx2zHdZNwqGA6Kz7gsm",
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    # return json.loads(response.text)['users'][0]['userId']
    try:
        data = json.loads(response.text)["users"][0]
        try:
            return data["userId"]
        except:
            return -1
    except:
        return -1


# Function to find the number of courses that the user has seen
def la_progress(email_id):
    try:
        user_id = fetch_userid(email_id)
        url = f"https://census.prod.learnapp.com/kraken/users/{user_id}/courses"
        payload = {}
        headers = {
            "authorization": token,
            "x-api-key": "Ch2rqJp3rxH8ZVccQT8ywV7zMR3Ac8fQ",
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        data = json.loads(response.text)["progress"]
        return data

    except:
        return -1


# Function to get the key of any value in dictionary
def get_key(val):
    for key, value in courses.items():
        if val == value:
            return key


# Code for fetching LA data and selecting the courses in the cohort
content_data = get_learnapp_content()

courses = {}
courses_list = st.multiselect(
    " Create a module by selecting any course/class/workshop/advanced course",
    content_data.keys(),
)

courses = {i: content_data[i]["id"] for i in content_data if i in courses_list}
st.write("")

# Code to get the list of users
user_data = st.file_uploader(
    "Upload a csv file with the Email ID of users in the cohort"
)
st.write("")

if user_data is not None:

    # Can be used wherever a "file-like" object is accepted:
    user_data = pd.read_csv(user_data)

# Code to get the module completion % of users
if st.button("Find Completion %"):
    st.write("")

    user_email = []

    for i in user_data["Email"]:
        user_email.append(i)

    user_progress = {}

    p_time = 0
    email_len = len(user_email)

    my_bar = st.progress(p_time)

    for user in user_email:
        user = user.strip().lower()
        b = {}
        try:
            a = la_progress(user)
            for i in a:
                try:
                    if i["courseId"] in list(courses.values()):
                        b.update({get_key(i["courseId"]): i["percentage"]})
                except:
                    continue
            user_progress[user] = b
            p_time += 1
            my_bar.progress(p_time / email_len)
        except:
            p_time += 1
            continue

    df_progress = pd.DataFrame(user_progress).T
    df_progress.fillna(0, inplace=True)

    my_bar.empty()

    df_progress["completion %"] = df_progress.mean(axis=1)

    completed_users = df_progress[df_progress["completion %"] >= 75][
        "completion %"
    ].count()
    st.metric("Completion Rate", f"{round(completed_users * 100 / email_len, 2)}%")
    st.write("----")
    st.subheader("Visualize Data")
    st.dataframe(df_progress)
    st.write("----")

    # code to download it as csv
    st.subheader("Donwload File")

    @st.cache
    def convert_df(df):
        # IMPORTANT: Cache the conversion to prevent computation on every rerun
        return df.to_csv().encode("utf-8")

    csv = convert_df(df_progress)

    st.download_button(
        label="Download CSV",
        data=csv,
        file_name="cohort_completion.csv",
        mime="text/csv",
    )
