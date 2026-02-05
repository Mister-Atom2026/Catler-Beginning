# Catler-Beginning

Kivy-прототип меню гри з:
- intro/video screen;
- головним меню з кнопками Play / Settings / Exit;
- VHS-постобробкою в меню;
- екраном налаштувань (гучність + перемикач мови UA/EN);
- попапом підтвердження виходу зі звуком.

## Запуск (Windows/Linux/macOS)

```bash
python main.py
```

## Збірка APK через Buildozer

1. Встановити Buildozer:
   ```bash
   pip install buildozer
   ```
2. Ініціалізувати конфіг:
   ```bash
   buildozer init
   ```
3. Відредагувати `buildozer.spec` (`title`, `package.name`, `requirements = kivy[full]`, тощо).
4. Зібрати debug APK:
   ```bash
   buildozer -v android debug
   ```
5. Зібрати release:
   ```bash
   buildozer android release
   ```

## iOS

Для iOS потрібен macOS і toolchain `kivy-ios`.
