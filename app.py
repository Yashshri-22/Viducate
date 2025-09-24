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

def quiz(url):
    """
    Uses Google Gemini model to create a quiz based on the transcript.
    Fully free, replaces OpenAI GPT model.
    """
    transcript = get_transcript(url)
    model = genai.GenerativeModel("gemini-1.5-flash") 
    response = model.generate_content(
        f"Create a quiz based on the following transcript:\n\n{transcript}"
    )
    return response.text.strip()



with gr.Blocks(css="""
    body { font-family: 'Poppins', sans-serif; background: #f0f3f9; }
    .navbar { background: #2d6cdf; color: #fff; padding: 20px 40px 10px 40px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(45,108,223,0.10); border-radius: 0; }
    .navbar .logo { font-weight: 700; font-size: 27px; }
    .navbar ul { list-style: none; display: flex; gap: 30px; margin: 0; padding: 0; }
    .navbar ul li a { color: #fff; text-decoration: none; font-weight: 500; font-size: 17px; opacity: 0.95; }
    .navbar ul li a:hover { opacity: 1; text-decoration: underline; }
    .hero { max-width: 800px; margin: 48px auto 0 auto; padding: 0 14px; text-align: center; }
    .hero h1 { font-size: 48px; font-weight: 700; margin-bottom: 11px; color: #23447e; }
    .hero .subtitle { color: #455068; max-width: 550px; margin: 0 auto 34px auto; font-size: 19px; line-height: 1.4; }
    .super-card { background: #fff; border-radius: 18px; padding: 42px 36px 30px 36px; box-shadow: 0 12px 38px rgba(119,140,174,0.09); max-width: 480px; margin: 26px auto 0 auto; display: flex; flex-direction: column; align-items: center; }
    .summarize-btn { background: linear-gradient(90deg,#2176fd,#49a9e8 85%); color: #fff; border: none; padding: 17px 56px; border-radius: 22px; font-size: 20px; font-weight: 600; cursor: pointer; margin: 0 auto; transition: background 0.19s, box-shadow 0.15s; box-shadow: 0 5px 25px rgba(33,118,253,0.09); letter-spacing: 1px; }
    .summarize-btn:hover { background: linear-gradient(90deg,#1658aa,#2176fd 70%); box-shadow: 0 7px 32px rgba(33,118,253,0.12); }
    #summary-section { display: none; max-width: 440px; margin: 34px auto 0 auto; background: #f7f9fc; padding: 36px 27px 32px 27px; border-radius: 16px; border: 1.5px solid #e4e9f2; text-align: center; }
    #summary-section h3 { font-size: 24px; font-weight: 600; margin-bottom: 14px; }
    #summary-text { color: #333; font-size: 17px; }
    .quiz-btn { margin-top: 23px; display: inline-block; background: #22c35c; color: #fff; padding: 15px 0; width: 165px; border-radius: 9px; font-weight: 600; font-size: 17px; text-decoration: none; text-align: center; border: none; }
    .quiz-btn:hover { background: #189a40; }
""") as demo:

    # Navbar
    with gr.Row(elem_classes="navbar"):
        gr.Markdown("<div class='logo'>VidQuiz</div>")
        gr.Markdown("<ul><li><a href='#'>Home</a></li><li><a href='#'>About</a></li><li><a href='#'>Contact</a></li></ul>")

    # Hero section
    with gr.Column(elem_classes="hero"):
        gr.Markdown("<h1>Video Summarizer + Quiz</h1>")
        gr.Markdown("<div class='subtitle'>Instantly summarize any YouTube video and test yourself with AI-powered quizzes.<br><span style='font-size:15px;color:#508fd6;font-weight:500;'>Paste a video link to start.</span></div>")

    # URL input card
    with gr.Column(elem_classes="super-card"):
        url_input = gr.Textbox(label="", placeholder="Paste YouTube video link here", interactive=True)
        summarize_btn = gr.Button("Summarize", elem_classes="summarize-btn")

    # Summary and Quiz output
    summary_out = gr.Textbox(label="AI Video Summary", placeholder="Your AI-generated summary will appear here.", interactive=False, elem_classes="summary-section")
    quiz_btn = gr.Button("Play Quiz", elem_classes="quiz-btn")

    # Button functions
    summarize_btn.click(fn=summarize_transcript, inputs=url_input, outputs=summary_out)
    quiz_btn.click(fn=quiz, inputs=url_input, outputs=summary_out)

demo.launch()