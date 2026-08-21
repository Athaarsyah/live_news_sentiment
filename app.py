import os
import warnings

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from dotenv import load_dotenv
from textblob import TextBlob

warnings.filterwarnings("ignore")
load_dotenv()

API_KEY = os.getenv("NEWS_API_KEY")

st.set_page_config(
  page_title="Live News Sentiment Analysis Dashboard",
  layout="wide",
)

st.title("Live News Sentiment Analysis Dashboard")
st.markdown(
  "Track real-time sentiment of global news headlines using Python, NewsAPI, and Streamlit."
)
default_topics = [
  "Artificial Intelligence",
  "Bitcoin",
  "Tesla",
  "Microsoft",
  "OpenAI",
  "NVIDIA",
  "Claude",
]

if "topics" not in st.session_state:
  st.session_state.topics = default_topics.copy()

st.sidebar.header("Dashboard Controls")
new_topic = st.sidebar.text_input("Add a new topic").strip()

if st.sidebar.button("Add Topic") and new_topic and new_topic not in st.session_state.topics:
  st.session_state.topics.append(new_topic)
  st.rerun()

selected_topic = st.sidebar.selectbox("Choose Topic", st.session_state.topics)
article_limit = st.sidebar.slider("Number of Articles", 5, 50, 15)

if not API_KEY:
  st.error("NEWS_API_KEY is not configured. Add it to a .env file and restart the app.")
  st.stop()

try:
  response = requests.get(
    "https://newsapi.org/v2/everything",
    params={
      "q": selected_topic,
      "pageSize": article_limit,
      "sortBy": "publishedAt",
      "language": "en",
      "apiKey": API_KEY,
    },
    timeout=15,
  )
  response.raise_for_status()
  data = response.json()
except requests.RequestException as error:
  st.error(f"Unable to fetch news right now: {error}")
  st.stop()

if data.get("status") != "ok":
  st.error(data.get("message", "NewsAPI returned an unexpected response."))
  st.stop()

news_data = []
for article in data.get("articles", []):
  title = article.get("title")
  if not title or title == "[Removed]":
    continue

  polarity = TextBlob(title).sentiment.polarity
  if polarity > 0:
    sentiment = "Positive"
  elif polarity < 0:
    sentiment = "Negative"
  else:
    sentiment = "Neutral"

  news_data.append(
    {
      "Title": title,
      "Source": (article.get("source") or {}).get("name", "Unknown source"),
      "Published": (article.get("publishedAt") or "")[:10] or "Unknown date",
      "Sentiment": sentiment,
      "Polarity": polarity,
      "URL": article.get("url", "#"),
    }
  )

df = pd.DataFrame(news_data)
if df.empty:
  st.info(f"No usable headlines were found for {selected_topic}.")
  st.stop()

positive_count = (df["Sentiment"] == "Positive").sum()
negative_count = (df["Sentiment"] == "Negative").sum()
neutral_count = (df["Sentiment"] == "Neutral").sum()

col1, col2, col3 = st.columns(3)
col1.metric("Positive", positive_count)
col2.metric("Negative", negative_count)
col3.metric("Neutral", neutral_count)

fig = px.pie(
  df,
  names="Sentiment",
  title=f"Sentiment Distribution for {selected_topic}",
)
st.plotly_chart(fig, width='stretch', key="sentiment_distribution_chart")

hist_fig = px.histogram(
  df,
  x="Polarity",
  color="Sentiment",
  title="Headline Polarity Distribution",
)
st.plotly_chart(hist_fig, width='stretch', key="polarity_distribution_chart")

st.subheader("Latest Headlines")
for _, row in df.iterrows():
  st.markdown(f"### {row['Title']}")
  st.write(f"Source: {row['Source']} | Published: {row['Published']}")
  st.write(f"Sentiment: {row['Sentiment']} ({row['Polarity']:.2f})")
  if row["URL"] != "#":
    st.markdown(f"[Read full article]({row['URL']})")
  st.markdown("---")
col2.metric('Negative', negative_count)
col3.metric('Neutral', neutral_count)

fig = px.pie(
  df,
  names="Sentiment",
  title = f"Sentiment Distribution for {selected_topic}"
)

st.plotly_chart(fig, use_container_width=True)

hist_fig = px.histogram(
  df,
  x = "Polarity",
  color = "Sentiment",
  title = "Headline Polaroty Distibution"
)

st.plotly_chart(hist_fig, use_container_width=True)

st.subheader("latest headline")

for index, row in df.iterrows():
  st.markdown(f"### {row['Title']}")
  st.write(f"Source: {row['Source']}")
  st.write(f"Published: {row['Published']}")
  st.write(f"Sentiment: {row['Sentiment']}")
  st.markdown(f"[Read Full Article] ({row['URL']})")
  st.markdown("---")

  