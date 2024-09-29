import time
import os

import feedparser
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_mistralai.chat_models import ChatMistralAI

import flet as ft

explainer_text = """This is a demo application which analyzes a RSS feed \
and filter news aligned with the interests expressed by the user leveraging Mistral APIs. This app is \
provided AS-IS, without any warranty. It could be updated or removed at any point."""

prompt_interests = PromptTemplate.from_template(
"""You are an expert news analyst which needs to select news \
according to the user's interests. The user expressed the \
following interests: \

{interests}

Please establish whether the following news match the user's interests: \

{news}""")

def main(page: ft.Page):
    page.title = "RSS News Analyzer"
    page.scroll = "adaptive"


    class FitInterest(BaseModel):
        """Whether the news fit with user's interests."""
        fit_interests: bool = Field(description="Do the news fit the user's interest?")


    # Function definition
    def fetch_rss_feed(url):
        """Function that parses an RSS feed given the url
        """
        # Parse the RSS feed
        feed = feedparser.parse(url)
        records = []
        # add each entry to list
        for entry in feed.entries:
            new_entry = {}
            new_entry["title"] = entry.title
            new_entry["link"] = entry.link
            # Not all instance have a description
            try:
                new_entry["text"] = f"{entry.title}. {entry.description}"
            except Exception:
                new_entry["text"] = entry.title
            records.append(new_entry)
        return records


    def filter_news(news, interests):
        """Function that filters news according to the user's interests
        """
        secret_key = os.getenv("MISTRAL_API_KEY")
        # Setup LLM
        llm = ChatMistralAI(
            #model="open-mistral-nemo",
            model="mistral-large-latest",
            mistral_api_key=secret_key,
            temperature=0,
            max_retries=2,
            #cache=True,
        )
        structured_llm = llm.with_structured_output(FitInterest)
        partial_interests = prompt_interests.partial(interests=interests)
        interests_chain = partial_interests | structured_llm
        filtered_data = []
        for entry in news:
            time.sleep(1.5) # avoid rate limit, max 1 request per second
            selection = interests_chain.invoke(input={"news":entry["text"]})
            if selection.fit_interests:
                filtered_data.append(entry)
        return filtered_data

    def analyze_rss(e):
        """Function that analyzes a RSS feed given the url
        """
        # If no URL return an error
        if not rss_url.value:
            rss_url.error_text = "Please enter a RSS feed URL"
            page.update()
        elif not interests.value:
            interests.error_text = "Please enter a comma separated list of interests"
            page.update()
        else:
            progress = ft.AlertDialog(title=ft.ProgressBar(width=400))
            page.open(progress)
            # Get the url
            url = rss_url.value
            # Fetch the RSS feed
            records = fetch_rss_feed(url)
            if enable_filter.value:
                # Filter the news
                filtered_records = filter_news(records, interests.value)
                completion_message="News selection done!"
            else:
                filtered_records = records
                completion_message="News collection done!"
            # Remove previous results
            lv.controls = []
            for record in filtered_records:
                # Add new results
                lv.controls.append(
                    ft.Column(
                        controls=[
                            ft.Text(f"{record['title']}", size=25, weight=ft.FontWeight.BOLD),
                            ft.Text(f"{record['text']}", size=15),
                            ft.ElevatedButton(text="Read more", url=record['link']),
                            ft.Divider(),
                        ]
                ))
            
            alert = ft.AlertDialog(title=ft.Text(completion_message))
            page.open(alert)
            page.update()

    # Layout
    page.add(ft.SafeArea(ft.Text("RSS News Analyzer", size=50, weight=ft.FontWeight.BOLD)))
    
    page.add(ft.SafeArea(ft.Text(explainer_text)))

    page.add(ft.SafeArea(ft.Text("Enter RSS Feed URL:")))
    rss_url = ft.TextField(label="RSS Feed", value="https://www.ilsole24ore.com/rss/economia.xml")
    page.add(rss_url)
    enable_filter = ft.Switch(label="Filter news with AI?", value=True)
    page.add(enable_filter)
    page.add(ft.SafeArea(ft.Text("Insert a comma separated list of interests to filter news:")))
    interests = ft.TextField(label="Interests", value="agricolture, inflation")
    page.add(interests)
    page.add(ft.ElevatedButton("Analyze", on_click=analyze_rss))
    lv = ft.ListView(expand=True, spacing=10)
    page.add(lv)

ft.app(main)
