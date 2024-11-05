# Screenshot OCR Tool

スクリーンショットからテキストを抽出するシンプルなデスクトップアプリケーションです。OpenAIのGPT-4oを使用して、高精度なOCR（光学文字認識）を実現します。

## 機能

- 画面の特定領域をキャプチャ
- GPT-4oを使用したOCR処理
- 抽出されたテキストのクリップボードへのコピー
- シンプルで使いやすいGUIインターフェース
- Windows/macOSのクロスプラットフォーム対応

## インストール方法

1. リポジトリをクローン：
```bash
git clone https://github.com/hrtaym1114-github/LLM_OCR.git
cd LLM_OCR
```

2. 必要なパッケージをインストール：
```bash
poetry install
```

3. `.env`ファイルを作成し、OpenAI APIキーを設定：
```bash
OPENAI_API_KEY=your_api_key_here
```

## 使用方法

1. アプリケーションを起動：
```bash
python ./src/openai_ocr.py
```

2. 「Capture & OCR」ボタンをクリックし、テキストを抽出したい画面領域を選択
3. 抽出されたテキストが表示されます
4. 必要に応じて「Copy to Clipboard」ボタンでテキストをコピー

## 必要要件

- Python 3.8以上
- OpenAI API キー

## 依存パッケージ

- PyQt6
- openai
- Pillow
- python-dotenv

## ライセンス

MITライセンス

## 注意事項

- OpenAI APIの使用には料金が発生する場合があります
