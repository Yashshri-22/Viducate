import gradio as gr  
import re  
from youtube_transcript_api import YouTubeTranscriptApi
from langchain.text_splitter import RecursiveCharacterTextSplitter  
from langchain_community.vectorstores import FAISS 
from langchain.chains import LLMChain 
from langchain.prompts import PromptTemplate  
import openai
import os

def get_video_id(url):
    pattern = r'https:\/\/www\.youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

# url = ""
# video_id = get_video_id(url)
# print(video_id)
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_transcript(url):
    ytt_api = YouTubeTranscriptApi()
    video_id = get_video_id(url)
    transcripts = ytt_api.fetch(video_id)
    full_text = " ".join([snippet.text for snippet in transcripts.snippets])
    return full_text

transcript_generated = get_transcript("url")
print(transcript_generated)


# # Gradio UI
# with gr.Blocks() as demo:
#     gr.Markdown("# AI-Powered YouTube Summarizer & Q&A Tool")
#     url_in = gr.Textbox(label="YouTube Video URL")
#     summary_out = gr.Textbox(label="Video Summary")
#     question_in = gr.Textbox(label="Ask a question about the video")
#     answer_out = gr.Textbox(label="Answer")
#     state = gr.State()
#     gr.Button("Summarize Video").click(
#         summarize_video, inputs=url_in, outputs=summary_out
#     )
#     gr.Button("Ask Question").click(
#         answer_question, inputs=[url_in, question_in, state], outputs=[answer_out, state]
#     )

# demo.launch()

