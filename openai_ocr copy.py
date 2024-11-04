import pyautogui
import datetime
import tkinter as tk
from openai import OpenAI
import os
from PIL import Image, ImageGrab
import base64
import io
from dotenv import load_dotenv
import pyperclip

# .envファイルから環境変数を読み込む
load_dotenv()

class ScreenshotOCRTool:
    def __init__(self):
        # 環境変数からAPIキーを取得
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEYが設定されていません。.envファイルを確認してください。")
        
        self.client = OpenAI(api_key=api_key)
        self.start_x = None
        self.start_y = None
        self.current_rect = None
        self.setup_gui()
        
    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Screenshot OCR Tool")
        self.root.geometry("300x250")
        
        # ボタンフレームを作成（上部）
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5)
        
        # キャプチャーボタン
        capture_btn = tk.Button(button_frame, text="Capture & OCR", command=self.start_capture)
        capture_btn.pack(side=tk.LEFT, padx=5)
        
        # クリアボタン
        clear_btn = tk.Button(button_frame, text="Clear Text", command=self.clear_text)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # テキストエリア（中央）
        self.result_text = tk.Text(self.root, height=10, width=35)
        self.result_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # スクロールバーを追加
        scrollbar = tk.Scrollbar(self.root, command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=scrollbar.set)
        
        # コピーボタン（下部）
        copy_btn = tk.Button(self.root, text="Copy to Clipboard", command=self.copy_to_clipboard)
        copy_btn.pack(pady=5)

    def copy_to_clipboard(self):
        try:
            text = self.result_text.get(1.0, tk.END).strip()
            if text:
                pyperclip.copy(text)
                copy_btn = self.root.children['!button2']
                original_text = copy_btn['text']
                copy_btn['text'] = "Copied!"
                self.root.after(1000, lambda: copy_btn.configure(text=original_text))
        except Exception as e:
            print(f"クリップボードへのコピーに失敗しました: {e}")

    def start_capture(self):
        self.root.iconify()
        self.root.after(100, self.create_overlay)

    def create_overlay(self):
        # オーバーレイウィンドウを作成
        self.overlay = tk.Toplevel()
        self.overlay.attributes('-alpha', 0.3)  # 透明度を設定
        self.overlay.attributes('-fullscreen', True)
        self.overlay.attributes('-topmost', True)

        # キャンバスを作成
        self.canvas = tk.Canvas(self.overlay, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)

        # イベントをバインド
        self.canvas.bind('<Button-1>', self.on_press)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)

        # ESCキーでキャンセル
        self.overlay.bind('<Escape>', lambda e: self.cancel_capture())

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def on_drag(self, event):
        if self.current_rect:
            self.canvas.delete(self.current_rect)
        self.current_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y,
            outline='red', width=2
        )

    def on_release(self, event):
        if self.start_x is None or self.start_y is None:
            return

        # 座標を正規化（始点が終点より大きい場合に対応）
        x1 = min(self.start_x, event.x)
        y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x)
        y2 = max(self.start_y, event.y)

        # オーバーレイを閉じる
        self.overlay.destroy()

        # スクリーンショットを撮影
        self.capture_area(x1, y1, x2, y2)

    def cancel_capture(self):
        self.overlay.destroy()
        self.root.deiconify()
        
    def capture_area(self, x1, y1, x2, y2):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        
        # スクリーンショットを撮影
        screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        screenshot.save(filename)
        
        # OCR処理を実行
        text = self.perform_ocr(filename)
        
        # 結果を表示
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, text)
        
        # 一時ファイルを削除
        os.remove(filename)
        
        # メインウィンドウを復元
        self.root.deiconify()
    
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
        self.root.mainloop()

    def clear_text(self):
        """テキストエリアをクリアする"""
        self.result_text.delete(1.0, tk.END)
        # クリア完了を示すフィードバック
        self.root.after(100, lambda: self.show_feedback("Text Cleared!"))

    def show_feedback(self, message, duration=1000):
        """一時的なフィードバックメッセージを表示"""
        feedback_label = tk.Label(self.root, text=message, fg="green")
        feedback_label.pack(pady=2)
        self.root.after(duration, feedback_label.destroy)

if __name__ == "__main__":
    tool = ScreenshotOCRTool()
    tool.run()