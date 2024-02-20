# ai-bot-1
experimental AI bot

# 仕様メモ

1 ページ目
    API キー入力（OpenAIのキーを登録）
2 ページ目
    インストラクション入力（編集可能）
    対話履歴5回分保持
    Push - to - Talk 方式。ボタンを押すと聞き取り開始で、話が途切れると（無音を検出）API を呼び出し回答を得る
    回答が返ってきたら、自動再生。... したいのだが 何故か autoplay がうまくいかない。
    
    autoplay の参考はここから
    https://discuss.streamlit.io/t/how-to-play-an-audio-file-automatically-generated-using-text-to-speech-in-streamlit/33201