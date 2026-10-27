from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
import threading
import asyncio
import requests
import webbrowser
from streamget import DouyinLiveStream

class MiaoTingAndroid(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=30, spacing=20, **kwargs)
        
        self.add_widget(Label(text="秒听 · 抖音极速听", font_size=24, size_hint_y=None, height=60))
        
        self.url_input = TextInput(hint_text="粘贴直播间链接 (如 https://live.douyin.com/123)", multiline=False, size_hint_y=None, height=50)
        self.add_widget(self.url_input)
        
        self.cookie_input = TextInput(hint_text="Cookie (选填，留空自动获取)", multiline=True, size_hint_y=None, height=100)
        self.add_widget(self.cookie_input)
        
        self.btn = Button(text="🚀 一键提取并听声音", size_hint_y=None, height=60, background_color=(1, 0.3, 0.3, 1))
        self.btn.bind(on_press=self.start_task)
        self.add_widget(self.btn)
        
        self.status = Label(text="准备就绪", size_hint_y=None, height=40)
        self.add_widget(self.status)

    def start_task(self, instance):
        url = self.url_input.text.strip()
        if not url:
            self.show_popup("错误", "请填写直播间链接！")
            return
        
        self.status.text = "正在解析中..."
        self.btn.disabled = True
        threading.Thread(target=self.run_async, args=(url, self.cookie_input.text.strip()), daemon=True).start()

    def run_async(self, url, cookie):
        try:
            asyncio.run(self.fetch_url(url, cookie))
        except Exception as e:
            self.update_status(f"错误: {e}")
            self.enable_btn()

    async def fetch_url(self, url, cookie):
        if not cookie:
            self.update_status("正在自动获取游客凭证...")
            try:
                session = requests.Session()
                headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 13)"}
                session.get("https://live.douyin.com/", headers=headers, timeout=5)
                session.get(url, headers=headers, timeout=5)
                cookie = "; ".join([f"{k}={v}" for k, v in session.cookies.get_dict().items()])
            except:
                cookie = ""

        live = DouyinLiveStream(cookies=cookie)
        data = await live.fetch_web_stream_data(url)
        if not data:
            self.update_status("解析失败，主播可能未开播")
            self.enable_btn()
            return

        stream_obj = await live.fetch_stream_url(data, "OD")
        play_url = stream_obj.flv_url if stream_obj.flv_url else stream_obj.m3u8_url
        
        if play_url:
            self.update_status("✅ 解析成功！正在唤起播放器...")
            # 调用安卓系统浏览器/播放器打开流地址
            webbrowser.open(play_url)
            self.enable_btn()
        else:
            self.update_status("未找到流地址")
            self.enable_btn()

    def update_status(self, text):
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: setattr(self.status, 'text', text))

    def enable_btn(self):
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: setattr(self.btn, 'disabled', False))

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.8, 0.3))
        popup.open()

class MiaoTingApp(App):
    def build(self):
        return MiaoTingAndroid()

if __name__ == '__main__':
    MiaoTingApp().run()