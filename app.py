import gradio as gr
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_openai import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings

def get_transcript(url):
    from urllib.parse import urlparse, parse_qs
    video_id = parse_qs(urlparse(url).query)['v'][0]
    transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
    # Try to get English transcript; fallback to first
    try:
        transcript = transcripts.find_transcript(['en', 'en-US']).fetch()
    except:
        transcript = list(transcripts)[0].fetch()
    return " ".join([t['text'] for t in transcript])


# Summarization prompt
SUMMARY_PROMPT = PromptTemplate(
    input_variables=['transcript'],
    template="You are an expert AI assistant. Summarize the following video transcript for a student: {transcript}"
)

# Q&A prompt
QA_PROMPT = PromptTemplate(
    input_variables=['context', 'question'],
    template="You are an AI assistant providing detailed and accurate answers based on the following video context: {context}\nQuestion: {question}\nAnswer:"
)

llm = OpenAI(model="gpt-3.5-turbo", openai_api_key="api_key_here")

def summarize_video(url):
    transcript = get_transcript(url)
    chain = LLMChain(llm=llm, prompt=SUMMARY_PROMPT)
    summary = chain.run(transcript=transcript)
    return summary

# Create vector store for Q&A
def prepare_vectorstore(transcript):
    splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
    chunks = splitter.split_text(transcript)
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(chunks, embeddings)
    return vectorstore, chunks

def answer_question(url, question, state):
    if state is None or 'vectorstore' not in state:
        transcript = get_transcript(url)
        vectorstore, chunks = prepare_vectorstore(transcript)
        state = {'vectorstore': vectorstore, 'chunks': chunks}
    vectorstore = state['vectorstore']
    # Retrieve relevant chunk for question
    docs = vectorstore.similarity_search(question, k=3)
    context = " ".join([doc.page_content for doc in docs])
    chain = LLMChain(llm=llm, prompt=QA_PROMPT)
    answer = chain.run(context=context, question=question)
    return answer, state

# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("# AI-Powered YouTube Summarizer & Q&A Tool")
    url_in = gr.Textbox(label="YouTube Video URL")
    summary_out = gr.Textbox(label="Video Summary")
    question_in = gr.Textbox(label="Ask a question about the video")
    answer_out = gr.Textbox(label="Answer")
    state = gr.State()
    gr.Button("Summarize Video").click(
        summarize_video, inputs=url_in, outputs=summary_out
    )
    gr.Button("Ask Question").click(
        answer_question, inputs=[url_in, question_in, state], outputs=[answer_out, state]
    )

demo.launch()

