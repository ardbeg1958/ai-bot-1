from openai import OpenAI
import streamlit as st

import os
import time
import base64
from audio_recorder_streamlit import audio_recorder

# ページ遷移を管理するための関数
def go_to_page(page_name):
    st.session_state.current_page = page_name
    st.rerun()

def current_page_is(page_name):
    return st.session_state.current_page == page_name

# ChatBotクラスの定義
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
        "このアプリを使用するにはOpenAIのAPIキーを提供する必要があります。APIキーはOpenAIのダッシュボードで確認できます"
    )
    with st.form(key='my_form'):
        api_key = st.text_input('OpenAIのAPIキーを以下に入れて下さい:', '')
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
    # 音声ファイルのパス
    input_audio_file = "recorded_audio.wav"
    output_audio_file = "speech.mp3"

    # Streamlitのselectboxを使用してユーザーが選択できるようにする
    selected_model_name = st.selectbox("モデルを選択", MODEL_NAMES)
    selected_voice = st.selectbox("音声を選択", VOICES)
    if "user_input" not in st.session_state:
        st.session_state.user_input = "フレンドリーなやり取りを行って下さい"
        # st.session_state.user_input = "簡単な英文のシャドウイングを行います。ユーザーが「はじめて」と言ったら、簡単な英文を出してユーザーの言葉を聞いて下さい。ユーザーの言葉を聞いたらフィードバックを行い、次のシャドウイングの英文を出して下さい。「おわって」でシャドウイングを終わります"
        # st.session_state.user_input = "入力を「やさしい日本語」に変換して下さい。難しい単語や漢語は簡単なやまと言葉に変えて下さい"

    user_input = st.text_input("システムプロンプトを設定", value=st.session_state.user_input)

    if user_input:
        chatbot = initialize_chatbot(client, user_input, selected_model_name)
        audio_bytes = audio_recorder(text = "クリックして話す", 
                                     icon_name="microphone-lines",
                                     neutral_color="#6aa36f", pause_threshold=1.2)
        if audio_bytes:
            # st.audio(audio_bytes, format="audio/wav")
            write_audio_file(input_audio_file, audio_bytes)

            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=open(input_audio_file, "rb"),
            )
            st.write("入力:", transcript.text)

            # AIの応答を取得
            response_chatgpt = chatbot.get_ai_response(transcript.text)
            # 得られた応答を音声に変換
            response = client.audio.speech.create(
                model="tts-1", voice=selected_voice, input=response_chatgpt
            )
            # 応答を音声ファイルとして保存
            response.stream_to_file(output_audio_file)  

            # 応答を表示
            st.write("応答:", response_chatgpt)

            # 応答音声を再生
            data = read_audio_file(output_audio_file)
            st.audio(data, format="audio/mp3")
            # autoplay_audio(data)

            # transcript = client.audio.transcriptions.create(
            #     model="whisper-1",
            #     file=open(output_audio_file, "rb"),
            # )
            # st.write(transcript.text)


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

# @st.cache(allow_output_mutation=True)
def read_audio_file(file_path):
    with open(file_path, "rb") as audio_file:
        return audio_file.read()

def write_audio_file(file_path, audio_bytes):
    with open(file_path, "wb") as audio_file:
        audio_file.write(audio_bytes)
        audio_file.flush()
        os.fsync(audio_file.fileno())

# @st.cache_data(allows_output_mutation=True)
def autoplay_audio(data):
    if data:
        b64 = base64.b64encode(data).decode()
        # print(f"b64[0:10]: {b64[0:20]},{time.time()}")
        md = f"""
            <audio controls autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        placeholder = st.empty()
        placeholder.markdown(
            md,
            unsafe_allow_html=True,
        )   
        #st.markdown(
        #    md,
        #    unsafe_allow_html=True,
        #)

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