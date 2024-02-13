from openai import OpenAI
import streamlit as st
# from dotenv import load_dotenv
import os

# load_dotenv()

from audio_recorder_streamlit import audio_recorder

# ページ遷移を管理するための関数
def go_to_page(page_name):
    st.session_state.current_page = page_name
    st.rerun()

def current_page_is(page_name):
    return st.session_state.current_page == page_name

class ChatBot:
    def __init__(self, client, model_name, system_message, max_input_history=2):
        self.client = client
        self.model_name = model_name
        self.system_message = {"role": "system", "content": system_message}
        self.input_message_list = [self.system_message]
        self.max_input_history = max_input_history

    def add_user_message(self, message):
        self.input_message_list.append({"role": "user", "content": message})

    def get_ai_response(self, user_message):
        self.add_user_message(user_message)
        user_and_assisntant_message = self.input_message_list[1:]
        input_message_history = [self.system_message] + user_and_assisntant_message[
            -2 * self.max_input_history + 1 :
        ]
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=input_message_history,
            temperature=0.3,
        )
        ai_response = response.choices[0].message.content
        self.input_message_list.append({"role": "assistant", "content": ai_response})
        return ai_response
    
def get_api_key_page():
    st.title("OpenAI API Key")
    st.write(
        "To use this app, you need to provide your OpenAI API key. You can find your API key in the OpenAI dashboard."
    )
    with st.form(key='my_form'):
        api_key = st.text_input('Please Enter Your OpenAI Key below:', '')
        submit_button = st.form_submit_button(label='登録')
        if submit_button:
            st.session_state.api_key = api_key  # ユーザー入力をセッション状態に保存
            st.session_state.client = OpenAI(api_key=api_key) # client オブジェクトを保存
            go_to_page('chat_session')  # 2ページ目へ遷移

def chat_page():
    # client
    client = st.session_state.client
    # 利用可能なモデルと音声のリスト
    MODEL_NAMES = ["gpt-3.5-turbo-1106", "gpt-4-1106-preview"]
    VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

    # Streamlitのselectboxを使用してユーザーが選択できるようにする
    selected_model_name = st.selectbox("モデルを選択してください", MODEL_NAMES)
    selected_voice = st.selectbox("音声を選択してください", VOICES)
    if "user_input" not in st.session_state:
        # st.session_state.user_input = "フレンドリーなやり取りを行って下さい"
        # st.session_state.user_input = "入力を「やさしい日本語」に変換して下さい。難しい単語、漢語は簡単なやまと言葉に変えて下さい"
        st.session_state.user_input = "簡単な英文のシャドウイングを行います。ユーザーが「はじめて」と言ったら、簡単な英文を出してユーザーの言葉を聞いて下さい。ユーザーの言葉を聞いたらフィードバックを行い、次のシャドウイングの英文を出して下さい。「おわって」でシャドウイングを終わります"

    user_input = st.text_input("system promptを設定してください", value=st.session_state.user_input)

    if user_input:
        chatbot = initialize_chatbot(client, user_input, selected_model_name)
        audio_bytes = audio_recorder(text = "クリックして話し始めてください", pause_threshold=1.2)
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            write_audio_file("recorded_audio.wav", audio_bytes)

            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=open("recorded_audio.wav", "rb"),
            )
            st.text(transcript.text)

            response_chatgpt = chatbot.get_ai_response(transcript.text)
            response = client.audio.speech.create(
                model="tts-1", voice=selected_voice, input=response_chatgpt
            )

            # try:
            response.stream_to_file("speech.mp3")  
            #except Warning as w:
            #    print(f"Error: {w}")

            st.audio(read_audio_file("speech.mp3"), format="audio/mp3")

            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=open("speech.mp3", "rb"),
            )
            st.write(transcript.text)


def initialize_chatbot(client, user_input, selected_model_name):
    if "chatbot" not in st.session_state or st.session_state.user_input != user_input:
        st.session_state.chatbot = ChatBot(
            client,
            model_name=selected_model_name,
            system_message=user_input,
            max_input_history=5,
        )
        st.session_state.user_input = user_input
    return st.session_state.chatbot

def read_audio_file(file_path):
    with open(file_path, "rb") as audio_file:
        return audio_file.read()

def write_audio_file(file_path, audio_bytes):
    with open(file_path, "wb") as audio_file:
        audio_file.write(audio_bytes)

# ページ遷移のロジック
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'input_api_key'

if current_page_is('input_api_key'):
    get_api_key_page()
elif current_page_is('chat_session'):
    chat_page()
else:
    # APIキーが未検証または無効の場合は入力ページに戻る
    go_to_page('input_api_key')  # 1ページ目へ遷移