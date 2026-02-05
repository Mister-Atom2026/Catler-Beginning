import os

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.config import ConfigParser
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.effectwidget import EffectBase
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager

# Мовний словник
texts = {
    "uk": {
        "play": "Грати",
        "settings": "Налаштування",
        "exit": "Вихід",
        "volume": "Гучність",
        "language": "Мова",
        "ukrainian": "Українська",
        "english": "English",
        "save": "Зберегти та повернутися",
        "exit_confirm": "Ви впевнені, що хочете вийти?",
        "yes": "Так",
        "no": "Ні",
    },
    "en": {
        "play": "Play",
        "settings": "Settings",
        "exit": "Exit",
        "volume": "Volume",
        "language": "Language",
        "ukrainian": "Ukrainian",
        "english": "English",
        "save": "Save and Return",
        "exit_confirm": "Are you sure you want to exit?",
        "yes": "Yes",
        "no": "No",
    },
}


# VHS-ефект: зерно + scanlines
class VHSNoiseEffect(EffectBase):
    glsl = """
    uniform float time;

    vec4 effect(vec4 color, sampler2D texture, vec2 tex_coords, vec2 pixel_coords)
    {
        vec4 original = texture2D(texture, tex_coords);

        float noise = fract(sin(dot(tex_coords + vec2(time * 0.08, time * 0.03), vec2(12.9898, 78.233))) * 43758.5453);
        float grain_strength = 0.09;
        original.rgb += (noise - 0.5) * grain_strength;

        float scanline = sin(pixel_coords.y * 3.14159) * 0.04;
        original.rgb -= scanline;

        return original;
    }
    """


# Текстова кнопка з анімацією при натисканні
class GameButton(ButtonBehavior, Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._base_size = self.font_size
        self._base_color = tuple(self.color)

    def on_press(self):
        Animation.cancel_all(self)
        press_color = (
            self._base_color[0],
            self._base_color[1],
            self._base_color[2],
            0.8,
        )
        anim = Animation(font_size=self._base_size * 1.08, color=press_color, duration=0.12)
        anim.start(self)

    def on_release(self):
        Animation.cancel_all(self)
        anim = Animation(font_size=self._base_size, color=self._base_color, duration=0.12)
        anim.start(self)


class IntroScreen(Screen):
    def on_pre_enter(self):
        app = App.get_running_app()
        source = app.get_video_path("intro_video.mp4")
        try:
            if source and os.path.exists(source):
                self.ids.video.source = source
                self.ids.video.state = "play"
                self.ids.video.options = {"eos": "stop", "allow_stretch": True}
            else:
                self.manager.current = "menu"
        except Exception:
            self.manager.current = "menu"

    def on_enter(self):
        self.ids.video.bind(state=self.on_video_state)
        try:
            self.ids.video.bind(eos=self.on_video_eos)
        except Exception:
            pass

    def on_video_eos(self, *args):
        self.manager.current = "menu"

    def on_video_state(self, instance, value):
        if value == "stop":
            self.manager.current = "menu"


class GameScreen(Screen):
    def on_pre_enter(self):
        self.ids.video.bind(state=self.on_video_state)
        try:
            self.ids.video.bind(eos=self.on_video_eos)
        except Exception:
            pass

    def on_video_eos(self, *args):
        self.manager.current = "menu"

    def on_video_state(self, instance, value):
        if value == "stop":
            self.manager.current = "menu"
            # Тут буде основна логіка гри


class SettingsScreen(Screen):
    pass


class MenuScreen(Screen):
    vhs_effect = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.vhs_effect = VHSNoiseEffect()
        self._noise_event = None
        self._flicker_event = None

    def on_enter(self):
        self.update_texts()
        if self._noise_event is None:
            self._noise_event = Clock.schedule_interval(self.update_effect_time, 1 / 24)
        if self._flicker_event is None:
            self._flicker_event = Clock.schedule_interval(self.flicker_image, 100)

    def on_leave(self):
        if self._noise_event is not None:
            self._noise_event.cancel()
            self._noise_event = None
        if self._flicker_event is not None:
            self._flicker_event.cancel()
            self._flicker_event = None

    def update_effect_time(self, dt):
        t = self.vhs_effect.uniforms.get("time", 0.0)
        self.vhs_effect.uniforms["time"] = t + dt

    def flicker_image(self, dt):
        anim = Animation(opacity=1, duration=0.2) + Animation(opacity=0, duration=0.3)
        anim.start(self.ids.bg2)

    def update_texts(self):
        app = App.get_running_app()
        self.ids.play_btn.text = app.texts[app.current_lang]["play"]
        self.ids.settings_btn.text = app.texts[app.current_lang]["settings"]
        self.ids.exit_btn.text = app.texts[app.current_lang]["exit"]

    def play_game(self):
        app = App.get_running_app()
        source = app.get_video_path(f"game_start_video_{app.current_lang}.mp4")
        game_screen = self.manager.get_screen("game")
        try:
            if source and os.path.exists(source):
                game_screen.ids.video.source = source
                game_screen.ids.video.state = "play"
                self.manager.current = "game"
        except Exception:
            pass

    def show_exit_popup(self):
        app = App.get_running_app()

        content = BoxLayout(orientation="vertical", spacing="30dp", padding="30dp")
        content.add_widget(
            Label(
                text=app.texts[app.current_lang]["exit_confirm"],
                font_name="assets/custom.ttf",
                font_size="42sp",
                color=(1, 1, 1, 1),
            )
        )

        btn_box = BoxLayout(orientation="horizontal", spacing="50dp", size_hint_y=None, height="100dp")
        yes_btn = GameButton(
            text=app.texts[app.current_lang]["yes"],
            color=(1, 0, 0, 1),
            font_name="assets/custom.ttf",
            font_size="56sp",
        )
        no_btn = GameButton(
            text=app.texts[app.current_lang]["no"],
            color=(1, 1, 1, 1),
            font_name="assets/custom.ttf",
            font_size="56sp",
        )

        btn_box.add_widget(yes_btn)
        btn_box.add_widget(no_btn)
        content.add_widget(btn_box)

        popup = Popup(title="", content=content, size_hint=(0.8, 0.6), separator_height=0)
        yes_btn.bind(on_press=lambda *_: self.exit_game(popup))
        no_btn.bind(on_press=lambda *_: popup.dismiss())
        popup.open()

    def exit_game(self, popup):
        app = App.get_running_app()
        sound = SoundLoader.load("assets/exit_sound.wav")
        if sound:
            sound.volume = app.volume
            sound.play()
        popup.dismiss()
        app.stop()


KV = """
#:import dp kivy.metrics.dp

<GameButton>:
    font_name: "assets/custom.ttf"
    font_size: "60sp"
    bold: True
    size_hint: 0.5, 0.15
    halign: "center"
    valign: "middle"
    text_size: self.size

<IntroScreen>:
    Video:
        id: video
        size: root.size
        pos: root.pos
        allow_stretch: True
        keep_ratio: False

<GameScreen>:
    Video:
        id: video
        size: root.size
        pos: root.pos
        allow_stretch: True
        keep_ratio: False

<SettingsScreen>:
    FloatLayout:
        canvas.before:
            Color:
                rgba: 0, 0, 0, 1
            Rectangle:
                size: self.size
                pos: self.pos

        BoxLayout:
            orientation: "vertical"
            size_hint: 0.8, 0.8
            pos_hint: {"center_x": 0.5, "center_y": 0.5}
            spacing: "40dp"
            padding: "40dp"

            Label:
                text: app.texts[app.current_lang]["settings"]
                font_name: "assets/custom.ttf"
                font_size: "80sp"
                color: 1, 0, 0, 1

            Label:
                text: app.texts[app.current_lang]["volume"]
                font_name: "assets/custom.ttf"
                font_size: "50sp"
                color: 1, 1, 1, 1
                size_hint_y: None
                height: "60dp"

            Slider:
                min: 0
                max: 100
                value: app.volume * 100
                step: 1
                on_value: app.set_volume(self.value)

            Label:
                text: app.texts[app.current_lang]["language"]
                font_name: "assets/custom.ttf"
                font_size: "50sp"
                color: 1, 1, 1, 1
                size_hint_y: None
                height: "60dp"

            BoxLayout:
                orientation: "horizontal"
                spacing: "30dp"
                size_hint_y: None
                height: "80dp"

                ToggleButton:
                    text: app.texts[app.current_lang]["ukrainian"]
                    group: "lang"
                    state: "down" if app.current_lang == "uk" else "normal"
                    on_state: app.set_lang("uk") if self.state == "down" else None

                ToggleButton:
                    text: app.texts[app.current_lang]["english"]
                    group: "lang"
                    state: "down" if app.current_lang == "en" else "normal"
                    on_state: app.set_lang("en") if self.state == "down" else None

            GameButton:
                text: app.texts[app.current_lang]["save"]
                color: 1, 0, 0, 1
                on_press: root.manager.current = "menu"

<MenuScreen>:
    FloatLayout:
        canvas.before:
            Color:
                rgba: 0, 0, 0, 1
            Rectangle:
                size: self.size
                pos: self.pos

        EffectWidget:
            size: root.size
            pos: root.pos
            effects: [root.vhs_effect]

            FloatLayout:
                Image:
                    id: bg1
                    source: "assets/menu_bg_1.png"
                    size_hint: 0.65, 0.85
                    pos_hint: {"center_x": 0.70, "center_y": 0.50}
                    allow_stretch: True
                    keep_ratio: False

                Image:
                    id: bg2
                    source: "assets/menu_bg_2.png"
                    size_hint: 0.65, 0.85
                    pos_hint: {"center_x": 0.70, "center_y": 0.50}
                    allow_stretch: True
                    keep_ratio: False
                    opacity: 0

                Label:
                    text: "Catler: Beginning"
                    font_name: "assets/custom.ttf"
                    font_size: "100sp"
                    bold: True
                    color: 1, 0, 0, 1
                    pos_hint: {"center_x": 0.5, "top": 0.95}

                BoxLayout:
                    orientation: "vertical"
                    size_hint: 0.5, 0.5
                    pos_hint: {"center_x": 0.3, "center_y": 0.5}
                    spacing: "50dp"

                    GameButton:
                        id: play_btn
                        color: 1, 0, 0, 1
                        on_press: root.play_game()

                    GameButton:
                        id: settings_btn
                        color: 1, 1, 1, 1
                        on_press: root.manager.current = "settings"

                    GameButton:
                        id: exit_btn
                        color: 1, 0, 0, 1
                        on_press: root.show_exit_popup()
"""

Builder.load_string(KV)


class CatlerApp(App):
    current_lang = StringProperty("uk")

    def build(self):
        Window.fullscreen = "auto"

        # Автоматично створюємо папки для ресурсів/відео
        os.makedirs("assets", exist_ok=True)
        os.makedirs(os.path.join("assets", "videos"), exist_ok=True)

        # Налаштування
        self.config = ConfigParser()
        self.config.read("settings.ini")

        if not self.config.has_section("lang"):
            self.config.add_section("lang")
            self.config.set("lang", "current", "uk")
        if not self.config.has_section("sound"):
            self.config.add_section("sound")
            self.config.set("sound", "volume", "80")

        self.config.write()

        self.current_lang = self.config.get("lang", "current")
        self.volume = float(self.config.get("sound", "volume")) / 100
        self.texts = texts

        sm = ScreenManager()
        sm.add_widget(IntroScreen(name="intro"))
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(GameScreen(name="game"))

        Clock.schedule_once(lambda dt: self.check_intro(sm), 0.2)
        return sm

    def get_video_path(self, filename):
        candidates = [
            os.path.join("assets", filename),
            os.path.join("assets", "videos", filename),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    def check_intro(self, sm):
        try:
            if sm.current == "intro" and sm.get_screen("intro").ids.video.state != "play":
                sm.current = "menu"
        except Exception:
            sm.current = "menu"

    def set_lang(self, lang):
        if lang != self.current_lang:
            self.current_lang = lang
            self.config.set("lang", "current", lang)
            self.config.write()
            if self.root:
                self.root.get_screen("menu").update_texts()

    def set_volume(self, value):
        self.volume = value / 100
        self.config.set("sound", "volume", str(int(value)))
        self.config.write()


if __name__ == "__main__":
    CatlerApp().run()

# Інструкція:
# • Запуск на ПК/Windows/Linux/macOS: python main.py
# • Збірка APK для Android через Buildozer:
#   1. pip install buildozer
#   2. buildozer init
#   3. Відредагуйте buildozer.spec (title, package.name, requirements = kivy[full])
#   4. buildozer -v android debug
#   5. Для релізу: buildozer android release
# • Для iOS потрібен macOS та kivy-ios toolchain.
