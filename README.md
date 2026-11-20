# Hostel Alarm

**Простое Android-приложение для мониторинга** — пример проекта, созданного полностью локально с помощью AI-агента.

## Как написан этот проект

Весь код написан и отлажен **Hermes Agent** — AI-агентом, который работает с локальной LLM:

| Компонент | Значение |
|---|---|
| Модель | Qwen3.6-35B-A3B (UD-Q4_K_M, int4 квантование) |
| Сервер | [PolyStrata](https://github.com/simplexai-labs/PolyStrata) |
| GPU | NVIDIA GeForce RTX 3060 (12 ГБ VRAM) |
| CPU | AMD Ryzen 7 3700X |
| RAM | 64 ГБ |
| Скорость | ~80 токенов/сек |

Ничего не уходит в облако — всё работает на локальной машине.

## Навык (Skill) для Hermes

В папке `hermes/` лежит `SKILL.md` — инструкция для Hermes Agent по работе с BeeWare/Briefcase и сборке Android-приложений.

**Установка в Hermes:**
1. Скопируйте `hermes/SKILL.md` в `~/.hermes/skills/beeware-briefcase/SKILL.md`
2. Или используйте команду `skill_manage` для регистрации навыка

Навык содержит:
- Пошаговые инструкции по сборке APK через Briefcase
- Рабочие паттерны для Toga-приложений на Android
- Обход известных проблем (Chaquopy, ToneGenerator, логирование)
- Методы тестирования на эмуляторе и физическом устройстве

## Возможности агента

### Эмулятор и визуальная отладка
Hermes Agent может полностью автономно тестировать Android-приложения:
- Запуск Android-эмулятора через ADB
- Скриншоты экрана и анализ UI
- Нажатие кнопок и ввод данных через `adb shell input`
- Чтение logcat для отладки
- Итеративный цикл: исправил → собрал → установил → проверил

### Сборка и установка на телефон
- Сборка debug-APK из исходного кода
- Установка на подключённый телефон через `adb install`

**Как включить отладку по USB на Android:**
1. Настройки → О телефоне → нажимайте «Номер сборки» 7 раз до появления «Вы стали разработником»
2. Настройки → Для разработчиков → включите «Отладка по USB»
3. Подключите телефон кабелем — на экране появится запрос на разрешение, нажмите «Разрешить»

## Приложение

**Hostel Alarm** — минимальное Android-приложение на BeeWare/Toga, которое:
- Опрашивает Zabbix API каждые 5 секунд
- Отслеживает значение `stars_count_0`
- При падении ниже порога запускает звуковую сирену через нативный Android `ToneGenerator`
- Показывает текущее значение, количество тиков и статус на экране

Проект демонстрирует полный цикл разработки Android-приложения с нуля: от написания кода AI-агентом до сборки, установки и тестирования — полностью локально, без облачных сервисов.

## Структура проекта

```
HostelAlarm/
├── src/HostelAlarm/     # Исходный код приложения
│   ├── app.py           # Основной код (UI, опрос, логика)
│   ├── zabbix.py        # Клиент Zabbix API
│   ├── alarm.py         # Менеджер звука (ToneGenerator)
│   ├── android_logger.py # Логирование в Android Logcat
│   └── mock_zabbix.py   # Mock-сервер для тестов
├── hermes/              # Навыки для Hermes Agent
│   └── SKILL.md         # Инструкция по сборке Android-приложений
├── pyproject.toml       # Конфигурация Briefcase
└── README.md            # Этот файл
```

## Сборка

```bash
# Установка зависимостей
python -m pip install briefcase

# Сборка APK
briefcase build android --debug

# Установка на устройство
adb install -r build/HostelAlarm/android/gradle/app/build/outputs/apk/debug/app-debug.apk
```

## Эмулятор Android

### Установка Android SDK и AVD Manager

```bash
# Установите Android SDK через Android Studio или командной строкой:
# SDK устанавливается в ~/Android/Sdk (Linux/macOS) или
# C:\Users\<user>\AppData\Local\Android\Sdk (Windows)

# Проверьте доступные системные образы:
ls $ANDROID_HOME/system-images/

# Создайте виртуальное устройство (AVD):
$ANDROID_HOME/cmdline-tools/latest/bin/avdmanager.bat create avd \
  -n HostelAlarm \
  -k "system-images;android-33;google_apis;x86_64" \
  --device "Nexus 6" \
  -f
```

### Запуск эмулятора

```bash
# Запуск без графического окна (для автоматизации):
$ANDROID_HOME/emulator/emulator.exe -avd HostelAlarm \
  -no-snapshot \
  -no-window \
  -no-audio \
  -gpu swiftshader_indirect

# Дождитесь загрузки:
$ANDROID_HOME/platform-tools/adb.exe wait-for-device
$ANDROID_HOME/platform-tools/adb.exe shell getprop sys.boot_completed
# Вернёт "1" когда эмулятор готов
```

### Остановка эмулятора

```bash
$ANDROID_HOME/platform-tools/adb.exe -s emulator-5554 emu kill
```

### Проверка подключения

```bash
# Список подключённых устройств
adb devices

# Должно показать:
# emulator-5554    device
```

### Скриншот и логирование

```bash
# Скриншот экрана
adb -s emulator-5554 exec-out screencap -p > screenshot.png

# Чтение логов приложения
adb -s emulator-5554 logcat -d -s HostelAlarm

# Все логи с Python
adb -s emulator-5554 logcat -d | grep -i "HostelAlarm\|python\|chaquopy"
```

### Сеть: доступ к хост-машине

Из эмулятора хост-машина доступна по адресу `10.0.2.2`.
Для доступа к сервисам в локальной сети настройте TCP-прокси на хосте
(см. `hermes/SKILL.md` — секция "Network access from emulator").

## Лицензия

BSD-3-Clause
