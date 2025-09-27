import json
import os
import gradio as gr  
import re  
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai

api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("Google API key not found in environment variables!")
genai.configure(api_key=api_key)

# --- Helper Functions ---
def get_video_id(url):
    pattern = r'https:\/\/www\.youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_transcript(url):
    ytt_api = YouTubeTranscriptApi()
    video_id = get_video_id(url)
    transcripts = ytt_api.fetch(video_id)
    full_text = " ".join([snippet.text for snippet in transcripts.snippets])
    print("\n--- TRANSCRIPT FETCHED ---\n")
    print(full_text)
    print("\n-------------------------\n")
    return full_text

def summarize_transcript(transcript_text):
    model = genai.GenerativeModel("gemini-1.5-flash") 
    response = model.generate_content(
        f"Summarize this transcript in a few paragraphs:\n\n{transcript_text}"
    )
    return response.text.strip()

def generate_quiz(url):
    transcript_text = get_transcript(url)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        """Respond ONLY with a valid JSON object in this format:
        {
          "quiz": [
            {"question": "...", "options": ["option1","option2","option3","option4"], "answer": "full text of the correct option"},
            ...
          ]
        }
        Important: **The 'answer' field must be exactly one of the 'options' strings, not letters.**
        Transcript:
        """ + transcript_text
    )
    quiz_json = response.text.strip()
    print("Model raw response:", quiz_json)  # Debug
    try:
        quiz_data = json.loads(quiz_json)
    except:
        import re
        match = re.search(r"\{.*\}", quiz_json, re.DOTALL)
        if match:
            quiz_json = match.group(0)
            quiz_data = json.loads(quiz_json)
        else:
            quiz_data = {"quiz": [
                {"question": "Error", "options": ["Error"], "answer": "Error"} for _ in range(5)
            ]}
    return quiz_data

def check_answers(user_answers, quiz_data):
    score = 0
    feedback = []
    for i, (ua, q) in enumerate(zip(user_answers, quiz_data["quiz"])):
        correct = q["answer"]
        if ua.strip().lower() == correct.strip().lower():
            score += 1
            feedback.append(f"Q{i+1}: Correct")
        else:
            feedback.append(f"Q{i+1}: Wrong (Correct: {correct})")
    return f"Your Score: {score}/{len(quiz_data['quiz'])}\n\n" + "\n".join(feedback)

# --- Chatbot Logic ---
current_transcript = ""

def set_transcript(url):
    """Fetch transcript and save to global variable."""
    global current_transcript
    current_transcript = get_transcript(url)
    return current_transcript

def chat_with_video(user_question):
    """Answer user questions based on the stored transcript."""
    if not current_transcript:
        return "⚠ Please load a video first using the Summarize or Quiz button."
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        f"You are an assistant. Answer the question using ONLY the following video transcript:\n\n"
        f"Transcript:\n{current_transcript}\n\n"
        f"Question: {user_question}"
    )
    return response.text.strip()

def display_quiz(url):
    quiz_data = generate_quiz(url)
    updates = []
    for i in range(5):
        q = quiz_data["quiz"][i]
        updates.append(gr.update(
            choices=q["options"],
            label=f"Q{i+1}: {q['question']}",
            value=None
        ))
    return updates + [quiz_data]

# --- Gradio UI (Updated Layout) ---
with gr.Blocks(css="""
    body { 
        font-family: 'Poppins', sans-serif; 
        margin: 0;
        padding: 0;
        transition: background 0.3s, color 0.3s;
    }
    /* Light theme */
    body.light { background: #f7f9fc; color: #1a1a1a; }
    body.light .navbar { background: #2d6cdf; color: #fff; }
    body.light .super-card, body.light .left-panel, body.light .right-panel, body.light .chat-panel { background: #fff; color: #222; }
    body.light #summary-text, body.light #quiz-text, body.light #chat-answer { background:#f0f3f9; color: #111; }
    /* Dark theme */
    body.dark { background: #121212; color: #f5f5f5; }
    body.dark .navbar { background: #1e3a8a; color: #fff; }
    body.dark .super-card, body.dark .left-panel, body.dark .right-panel, body.dark .chat-panel { background: #1f1f1f; color: #eaeaea; }
    body.dark #summary-text, body.dark #quiz-text, body.dark #chat-answer { background:#252525; color: #eee; }

    .navbar { padding: 16px 40px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(0,0,0,0.15); }
    .navbar .logo { font-weight: 700; font-size: 27px; }
    .navbar ul { list-style: none; display: flex; gap: 28px; margin: 0; padding-left: 450px; }
    .navbar ul li a { color: inherit; text-decoration: none; font-weight: 500; font-size: 16px; opacity: 0.9; }
    .navbar ul li a:hover { opacity: 1; text-decoration: underline; }

    .hero { max-width: 800px; margin: 50px auto 30px auto; padding: 0 20px; text-align: center; }
    .hero h1 { font-size: 46px; font-weight: 700; margin-bottom: 12px; }
    .hero .subtitle { max-width: 550px; margin: 0 auto 34px auto; font-size: 18px; line-height: 1.5; }

    .super-card { border-radius: 16px; padding: 32px 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); max-width: 500px; margin: 24px auto; display: flex; flex-direction: column; align-items: center; }
    .buttons-row { max-width: 500px; margin: 12px auto; display: flex; gap: 18px; justify-content: center; }
    .summarize-btn, .quiz-btn { border: none; padding: 12px 28px; border-radius: 12px; font-size: 17px; font-weight: 600; cursor: pointer; flex: 1; text-align: center; transition: 0.2s ease; }
    .summarize-btn { background: linear-gradient(90deg,#2176fd,#49a9e8 85%); color: #fff; }
    .summarize-btn:hover { background: linear-gradient(90deg,#1658aa,#2176fd 70%); }
    .quiz-btn { background: #22c35c; color: #fff; }
    .quiz-btn:hover { background: #189a40; }

    #bottom-grid { max-width: 1100px; margin: 40px auto; display: flex; gap: 24px; padding: 0 20px; }
    .left-panel, .right-panel, .chat-panel { border-radius: 14px; box-shadow: 0 6px 22px rgba(0,0,0,0.1); padding: 26px 20px; flex: 1; min-width: 0; }
    #summary-title, #quiz-title, #chat-title { font-size: 1.15rem; font-weight: 600; margin-bottom: 14px; }
    #summary-text, #quiz-text, #chat-answer { font-size: 1rem; min-height: 120px; border-radius: 6px; padding: 10px; }
""") as demo:

    # Navbar
    with gr.Row(elem_classes="navbar"):
        gr.Markdown("<div class='logo'>Viducate</div>")
        gr.Markdown("<ul><li><a href='http://127.0.0.1:5500/register.html' target='_blank'>Logout</a></li></ul>")
        
    # Hero section
    with gr.Column(elem_classes="hero"):
        gr.Markdown("<h1>Video Summarizer + Quiz</h1>")
        gr.Markdown("<div class='subtitle'>Instantly summarize any YouTube video and test yourself with AI-powered quizzes.<br>"
                    "<span style='font-size:15px;color:#508fd6;font-weight:500;'>Paste a video link to start.</span></div>")

    # URL input
    with gr.Column(elem_classes="super-card"):
        url_input = gr.Textbox(label="", placeholder="Paste YouTube video link here", interactive=True, scale=2)

    # Buttons row
    with gr.Row(elem_classes="buttons-row"):
        summarize_btn = gr.Button("Summarize", elem_classes="summarize-btn")
        quiz_btn = gr.Button("Play Quiz", elem_classes="quiz-btn")

    # Bottom grid
    with gr.Row(elem_id="bottom-grid"):
        # Left panel: summary + chat stacked
        with gr.Column(elem_classes="left-panel"):
            gr.Markdown("<div id='summary-title'>AI Video Summary</div>")
            summary_out = gr.Textbox(label="", placeholder="Your AI-generated summary will appear here.", interactive=False, lines=10, elem_id="summary-text")
            
            # Chat under summary
            with gr.Column(elem_classes="chat-panel"):
                gr.Markdown("<div id='chat-title'>Ask the Video</div>")
                chat_question = gr.Textbox(label="", placeholder="Type a question about the video")
                chat_btn = gr.Button("Ask")
                chat_answer = gr.Textbox(label="", placeholder="AI will answer here", interactive=False, lines=6, elem_id="chat-answer")

        # Right panel: quiz
        with gr.Column(elem_classes="right-panel"):
            gr.Markdown("<div id='quiz-title'>Video Quiz</div>")
            quiz_state = gr.State()
            q_radios = [gr.Radio(choices=[], label=f"Q{i+1}", type="value") for i in range(5)]
            submit_btn = gr.Button("Submit Answers")
            score_out = gr.Textbox(label="Results", lines=12, elem_id="quiz-text")

    # --- Wiring (unchanged) ---
    summarize_btn.click(fn=lambda url: summarize_transcript(set_transcript(url)), inputs=url_input, outputs=summary_out)
    quiz_btn.click(fn=display_quiz, inputs=url_input, outputs=q_radios + [quiz_state])

    def evaluate(*args):
        quiz_data = args[-1]
        user_answers = args[:-1]
        return check_answers(user_answers, quiz_data)

    submit_btn.click(fn=evaluate, inputs=q_radios + [quiz_state], outputs=score_out)
    chat_btn.click(fn=chat_with_video, inputs=chat_question, outputs=chat_answer)

demo.launch()
