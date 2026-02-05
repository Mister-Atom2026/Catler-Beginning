import os

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.config import ConfigParser
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.effectwidget import EffectBase, EffectWidget
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


# VHS-ефект (зерно + scanlines)
class VHSNoiseEffect(EffectBase):
    glsl = """
    uniform float time;
    uniform vec2 resolution;

    vec4 effect(vec4 color, sampler2D texture, vec2 tex_coords, vec2 pixel_coords) {
        vec4 original = texture2D(texture, tex_coords);

        // Зерно (noise)
        float noise = fract(sin(dot(tex_coords + time * 0.05, vec2(12.9898, 78.233))) * 43758.5453);
        original.rgb += (noise - 0.5) * 0.12;

        // Scanlines
        float scanline = sin(pixel_coords.y * 6.2831 / 3.0) * 0.08;
        original.rgb -= scanline;

        return original;
    }
    """


# Кнопка з hover-ефектом (збільшення + затемнення)
class GameButton(ButtonBehavior, Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._orig_color = tuple(self.color)
        self._orig_font_size = self.font_size

    def on_enter(self, *args):
        Animation(font_size=self._orig_font_size * 1.08, duration=0.2).start(self)
        dark_color = (
            self._orig_color[0] * 0.8,
            self._orig_color[1] * 0.8,
            self._orig_color[2] * 0.8,
            1,
        )
        Animation(color=dark_color, duration=0.2).start(self)

    def on_leave(self, *args):
        Animation(font_size=self._orig_font_size, duration=0.2).start(self)
        Animation(color=self._orig_color, duration=0.2).start(self)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.on_enter()
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self.on_leave()
        return super().on_touch_up(touch)


class IntroScreen(Screen):
    def on_pre_enter(self):
        try:
            if os.path.exists("assets/intro_video.mp4"):
                self.ids.video.source = "assets/intro_video.mp4"
                self.ids.video.state = "play"
                self.ids.video.options = {"eos": "stop", "allow_stretch": True}
            else:
                self.manager.current = "menu"
        except Exception:
            self.manager.current = "menu"

    def on_enter(self):
        self.ids.video.bind(state=self.on_video_state)

    def on_video_state(self, instance, value):
        if value == "stop":
            self.manager.current = "menu"


class GameScreen(Screen):
    def on_pre_enter(self):
        self.ids.video.bind(state=self.on_video_state)

    def on_video_state(self, instance, value):
        if value == "stop":
            self.manager.current = "menu"


class SettingsScreen(Screen):
    pass


class MenuScreen(Screen, EffectWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.vhs_effect = VHSNoiseEffect()
        self.effects = [self.vhs_effect]
        self._time_ev = None
        self._flicker_ev = None

    def on_enter(self):
        self.update_texts()
        if self._time_ev is None:
            self._time_ev = Clock.schedule_interval(self.update_time, 1 / 30)
        if self._flicker_ev is None:
            self._flicker_ev = Clock.schedule_interval(self.flicker_image, 10)

    def on_leave(self):
        if self._time_ev is not None:
            self._time_ev.cancel()
            self._time_ev = None
        if self._flicker_ev is not None:
            self._flicker_ev.cancel()
            self._flicker_ev = None

    def update_time(self, dt):
        current = self.vhs_effect.uniforms.get("time", 0.0)
        self.vhs_effect.uniforms["time"] = current + dt

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
        source = f"assets/game_start_video_{app.current_lang}.mp4"
        game_screen = self.manager.get_screen("game")
        try:
            if os.path.exists(source):
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
                font_size="50sp",
                color=(1, 1, 1, 1),
            )
        )

        btn_box = BoxLayout(
            orientation="horizontal", spacing="50dp", size_hint_y=None, height="100dp"
        )
        yes_btn = GameButton(
            text=app.texts[app.current_lang]["yes"], color=(1, 0, 0, 1), font_size="60sp"
        )
        no_btn = GameButton(
            text=app.texts[app.current_lang]["no"], color=(1, 1, 1, 1), font_size="60sp"
        )
        btn_box.add_widget(yes_btn)
        btn_box.add_widget(no_btn)
        content.add_widget(btn_box)

        popup = Popup(title="", content=content, size_hint=(0.8, 0.6), separator_height=0)
        yes_btn.bind(on_press=lambda *x: self.exit_game(popup))
        no_btn.bind(on_press=popup.dismiss)
        popup.open()

    def exit_game(self, popup):
        sound = SoundLoader.load("assets/exit_sound.wav")
        if sound:
            sound.volume = App.get_running_app().volume
            sound.play()
        popup.dismiss()
        App.get_running_app().stop()


KV = """
#:import dp kivy.metrics.dp

<GameButton>:
    halign: "center"
    valign: "middle"
    text_size: self.size
    size_hint_y: None
    height: dp(80)

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
                size: root.size
                pos: root.pos

        BoxLayout:
            orientation: "vertical"
            size_hint: 0.8, 0.8
            pos_hint: {"center_x": 0.5, "center_y": 0.5}
            spacing: "40dp"
            padding: "40dp"

            Label:
                text: app.texts[app.current_lang].get("settings", "Settings")
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
                id: volume_slider
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
                font_name: "assets/custom.ttf"
                font_size: "60sp"
                bold: True
                on_press: root.manager.current = "menu"

<MenuScreen>:
    FloatLayout:
        canvas.before:
            Color:
                rgba: 0, 0, 0, 1
            Rectangle:
                size: root.size
                pos: root.pos

        Image:
            id: bg1
            source: "assets/menu_bg_1.png"
            size_hint: 0.65, 0.85
            pos_hint: {"center_x": 0.7, "center_y": 0.5}
            allow_stretch: True
            keep_ratio: False

        Image:
            id: bg2
            source: "assets/menu_bg_2.png"
            size_hint: 0.65, 0.85
            pos_hint: {"center_x": 0.7, "center_y": 0.5}
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
            size_hint: 0.5, None
            height: self.minimum_height
            pos_hint: {"center_x": 0.3, "center_y": 0.5}
            spacing: "50dp"

            GameButton:
                id: play_btn
                color: 1, 0, 0, 1
                font_name: "assets/custom.ttf"
                font_size: "60sp"
                bold: True
                on_press: root.play_game()

            GameButton:
                id: settings_btn
                color: 1, 1, 1, 1
                font_name: "assets/custom.ttf"
                font_size: "60sp"
                bold: True
                on_press: root.manager.current = "settings"

            GameButton:
                id: exit_btn
                color: 1, 0, 0, 1
                font_name: "assets/custom.ttf"
                font_size: "60sp"
                bold: True
                on_press: root.show_exit_popup()
"""

Builder.load_string(KV)


class CatlerApp(App):
    current_lang = StringProperty("uk")

    def build(self):
        Window.fullscreen = "auto"

        self.config = ConfigParser()
        self.config.read("settings.ini")

        if not self.config.has_section("lang"):
            self.config.add_section("lang")
            self.config.set("lang", "current", "uk")
        if not self.config.has_section("sound"):
            self.config.add_section("sound")
            self.config.set("sound", "volume", "80")

        with open("settings.ini", "w", encoding="utf-8") as cfg:
            self.config.write(cfg)

        self.current_lang = self.config.get("lang", "current")
        self.volume = float(self.config.get("sound", "volume")) / 100
        self.texts = texts

        sm = ScreenManager()
        sm.add_widget(IntroScreen(name="intro"))
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(GameScreen(name="game"))

        Clock.schedule_once(lambda dt: self.check_intro(sm), 0.1)
        return sm

    def check_intro(self, sm):
        if sm.current == "intro" and sm.get_screen("intro").ids.video.state != "play":
            sm.current = "menu"

    def set_lang(self, lang):
        if lang != self.current_lang:
            self.current_lang = lang
            self.config.set("lang", "current", lang)
            with open("settings.ini", "w", encoding="utf-8") as cfg:
                self.config.write(cfg)
            if self.root:
                self.root.get_screen("menu").update_texts()

    def set_volume(self, value):
        self.volume = value / 100
        self.config.set("sound", "volume", str(int(value)))
        with open("settings.ini", "w", encoding="utf-8") as cfg:
            self.config.write(cfg)


if __name__ == "__main__":
    CatlerApp().run()
