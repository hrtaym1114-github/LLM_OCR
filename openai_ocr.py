import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, 
                            QVBoxLayout, QHBoxLayout, QTextEdit)
from PyQt6.QtCore import Qt, QTimer, QRect
from openai import OpenAI
import os
from PIL import Image, ImageGrab
import base64
import io
from dotenv import load_dotenv
import datetime
import subprocess

# .envファイルから環境変数を読み込む
load_dotenv()

class ScreenshotOCRTool(QMainWindow):
    def __init__(self):
        super().__init__()
        # 環境変数からAPIキーを取得
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEYが設定されていません。.envファイルを確認してください。")
        
        self.client = OpenAI(api_key=api_key)
        self.setup_gui()
        
    def setup_gui(self):
        self.setWindowTitle("Screenshot OCR Tool")
        self.setGeometry(100, 100, 400, 300)
        
        # メインウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # ボタンレイアウト
        button_layout = QHBoxLayout()
        
        # キャプチャーボタン
        capture_btn = QPushButton("Capture & OCR")
        capture_btn.clicked.connect(self.start_capture)
        button_layout.addWidget(capture_btn)
        
        # クリアボタン
        clear_btn = QPushButton("Clear Text")
        clear_btn.clicked.connect(self.clear_text)
        button_layout.addWidget(clear_btn)
        
        layout.addLayout(button_layout)
        
        # テキストエリア
        self.result_text = QTextEdit()
        layout.addWidget(self.result_text)
        
        # コピーボタン
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(copy_btn)
        
    def copy_to_clipboard(self):
        text = self.result_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            # フィードバック表示（一時的に）
            self.statusBar().showMessage("Copied!", 1000)
            
    def clear_text(self):
        self.result_text.clear()
        self.statusBar().showMessage("Text Cleared!", 1000)
        
    def start_capture(self):
        self.hide()
        QTimer.singleShot(100, self.create_overlay)

    def create_overlay(self):
        # オーバーレイウィンドウを作成
        self.overlay = QWidget()
        self.overlay.setWindowOpacity(0.3)
        self.overlay.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.overlay.setGeometry(0, 0, QApplication.primaryScreen().size().width(),
                                QApplication.primaryScreen().size().height())

        # 変数の初期化を追加
        self.start_x = None
        self.start_y = None
        self.current_rect = None

        # キャンバスを作成
        self.canvas = QWidget(self.overlay)
        self.canvas.setGeometry(0, 0, self.overlay.width(), self.overlay.height())
        self.canvas.setAutoFillBackground(True)
        self.canvas.setStyleSheet("background-color: transparent;")

        # イベントをバインド
        self.canvas.mousePressEvent = self.on_press
        self.canvas.mouseMoveEvent = self.on_drag
        self.canvas.mouseReleaseEvent = self.on_release

        self.overlay.show()

    def on_press(self, event):
        self.start_x = event.position().x()
        self.start_y = event.position().y()

    def on_drag(self, event):
        if not hasattr(self, 'start_x') or not hasattr(self, 'start_y'):
            return
        
        current_x = event.position().x()
        current_y = event.position().y()
        
        # スタイルシートの更新
        self.canvas.setStyleSheet("background-color: rgba(255, 0, 0, 0.3);")
        self.canvas.update()

    def on_release(self, event):
        if self.start_x is None or self.start_y is None:
            return

        # 座標を整数に変換して正規化
        x1 = int(min(self.start_x, event.pos().x()))
        y1 = int(min(self.start_y, event.pos().y()))
        x2 = int(max(self.start_x, event.pos().x()))
        y2 = int(max(self.start_y, event.pos().y()))

        # ���ーバーレイを閉じる
        self.overlay.close()

        # スクリーンショットを撮影
        self.capture_area(x1, y1, x2, y2)

    def cancel_capture(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.overlay.close()
            self.show()
        
    def capture_area(self, x1, y1, x2, y2):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        
        # 幅と高さを計算
        width = x2 - x1
        height = y2 - y1
        
        # macOSのscreencaptureコマンドを使用
        subprocess.run([
            'screencapture',
            '-x',  # サウンドなし
            '-R', f"{x1},{y1},{width},{height}",  # 領域を指定
            filename
        ])
        
        # OCR処理を実行
        text = self.perform_ocr(filename)
        
        # 結果を表示
        self.result_text.clear()
        self.result_text.insertPlainText(text)
        
        # 一時ファイルを削除
        os.remove(filename)
        
        # メインウィンドウを復元
        self.show()
    
    def image_to_base64(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def perform_ocr(self, image_path):
        base64_image = self.image_to_base64(image_path)
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "この画像内のテキストを抽出してください。レイアウトは無視して、テキストのみを出力してください。"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    
    def run(self):
        self.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tool = ScreenshotOCRTool()
    tool.run()
    sys.exit(app.exec())