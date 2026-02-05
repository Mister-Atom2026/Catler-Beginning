# Catler-Beginning

Kivy-прототип меню гри з:
- intro/video screen;
- головним меню з кнопками Play / Settings / Exit;
- VHS-постобробкою в меню;
- екраном налаштувань (гучність + перемикач мови UA/EN);
- попапом підтвердження виходу зі звуком.

## Запуск локально (Windows/Linux/macOS)

```bash
python main.py
```

## А як це запустити на GitHub?

Коротко: **GUI Kivy-додаток не запускається прямо в браузерному інтерфейсі GitHub** (там немає вікна застосунку).

Що можна робити на GitHub:

1. **Автоматично перевіряти код через GitHub Actions** (у цьому репо додано workflow `Python checks`, який запускає `python -m py_compile main.py`).
2. **Працювати в GitHub Codespaces** і запускати застосунок у терміналі контейнера (для реального GUI зазвичай зручніше локальна машина).
3. **Збирати Android APK у CI** (окремим workflow з Buildozer, якщо потрібно — можу додати).

### Перевірка в GitHub Actions

Після push у репозиторій:
- відкрий вкладку **Actions**;
- вибери workflow **Python checks**;
- переконайся, що джоба завершилась успішно.

## Збірка APK через Buildozer (локально або CI)

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
