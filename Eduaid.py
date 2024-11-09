#Imports: Libraries for PDF extraction, summarization, text-to-speech, and building the web app.
import streamlit as st #creates user interfaces for data apps
from PyPDF2 import PdfReader #extract the content of a PDF 
from transformers import pipeline #pre-trained model
#import pyttsx3 also text to speech (offline)
import tempfile #create and manage temporary files (tempfiles) and directories
from gtts import gTTS #google text to speech (online 'worked better')

#text extraction from uploaded PDF 
#Summarization Model
try: #this model is great for summarization(pre-trained) 
        summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
except Exception as e:
    st.error(f"Error loading summarization model: {e}")

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    return "".join(page.extract_text() for page in reader.pages)

#turns text into chunks and summarizes it (using the pre-trained model)
def split_text(text, max_tokens=450):
    sentences = text.split(". ")
    chunks, current_chunk = [], ""
    for sentence in sentences:
        if len(current_chunk.split()) + len(sentence.split()) > max_tokens:
            chunks.append(current_chunk)
            current_chunk = sentence
        else:
            current_chunk += " " + sentence
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

# Summarization function(summarize the text after splitting into chunks)
def summarize_text(text, max_words=400): # word limitation (takes 4-5 pages)
    chunks = split_text(text)
    summaries = []
    for chunk in chunks:
        try:
            summary = summarizer(chunk, max_length=max_words, min_length=max_words - 30, do_sample=False)
            summaries.append(summary[0]['summary_text'])
        except Exception as e:
            st.error(f"Error during summarization: {e}")
    return " ".join(summaries).strip()

#Text to audio using Google TTS (gTTS) 
#uses Google's cloud-based service.
def text_to_speech_gtts(text):
    tts = gTTS(text, lang='en')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as audio_file:
        tts.save(audio_file.name)
        audio_path = audio_file.name
    return audio_path

# Streamlit UI 
#simple interface for users to upload a PDF 
st.title("EduAid")
st.divider()
uploaded_file = st.file_uploader("Let me make you a podcast :)", type="pdf")
max_duration = 10  # Maximum duration for the audio
words_per_minute = 150 
duration_to_words = {minutes: (minutes * words_per_minute +1)for minutes in range(1, max_duration + 1)}

    #the user chooses the audio duration
summary_duration = st.slider("How long is your commute? (minutes):", 1, max_duration, 2)
if uploaded_file:
    st.write(f"Uploaded File: {uploaded_file.name}")
    
    with st.spinner("Extracting text..."):
        text = extract_text_from_pdf(uploaded_file)

    

    #Add 1 to the selected duration for generating a slightly longer summary
    adjusted_duration = summary_duration + 1
    max_words = duration_to_words[min(adjusted_duration, max_duration)]

    with st.spinner("Creating..."):
        summary = summarize_text(text, max_words=max_words)

    # Display summary in text
    st.write("### Podcast Script")
    st.write(summary)

    if st.button("Generate Podcast"):
        with st.spinner("Making your Podcast..."):
            audio_path = text_to_speech_gtts(summary)
        st.audio(audio_path, format="audio/mp3")
        st.success("Your podcast is ready!")
        st.download_button(label="Download Audio", data=open(audio_path, "rb"), file_name="summary_audio.mp3")