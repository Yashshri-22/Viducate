import os
import gradio as gr  
import re  
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

def get_video_id(url):
    pattern = r'https:\/\/www\.youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_transcript(url):
    ytt_api = YouTubeTranscriptApi()
    video_id = get_video_id(url)
    transcripts = ytt_api.fetch(video_id)
    full_text = " ".join([snippet.text for snippet in transcripts.snippets])
    return full_text

transcript_generated = get_transcript("url")
print(transcript_generated)

def summarize_transcript(transcript_text):
    """
    Uses Google Gemini model to summarize the full transcript into a short summary.
    Fully free, replaces OpenAI GPT model.
    """
    model = genai.GenerativeModel("gemini-1.5-flash") 
    response = model.generate_content(
        f"Summarize this transcript in a few paragraphs:\n\n{transcript_text}"
    )
    return response.text.strip()

def quiz(transcript_text):
    """
    Uses Google Gemini model to create a quiz based on the transcript.
    Fully free, replaces OpenAI GPT model.
    """
    model = genai.GenerativeModel("gemini-1.5-flash") 
    response = model.generate_content(
        f"Create a quiz based on the following transcript:\n\n{transcript_text}"
    )
    return response.text.strip()

summary_text = summarize_transcript(transcript_generated)
print("\n----- VIDEO SUMMARY -----\n")
print(summary_text)

quiz_text = quiz(transcript_generated)
print("\n----- VIDEO QUIZ -----\n")
print(quiz_text)