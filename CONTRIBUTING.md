# Як запропонувати виправлення / How to contribute

Почніть із [поточного випуску від 25 жовтня](source-updates/2026-10-25/README.md), [відкладених записів точного джерела](source-updates/2026-10-25/held-records.json.gz) або [результатів повторної перевірки попередніх 3 326 записів](source-updates/2026-10-25/held-resolution-outcomes.json.gz). Набір перекладів точного CC-CEDICT та окремі виправлення самого джерела мають різні показники. Старі черги від 15 жовтня й показники випуску від 19 жовтня залишаються історичними свідченнями.

Перегляньте відкриті issues та [створіть issue за шаблоном](https://github.com/MityaPolianskii/ukrainian-cedict/issues/new/choose). Вкажіть випуск, ID, джерельний набір (`original_corpus`, `app_baseline` або `upstream_refresh`), китайське слово, точний піньїнь, номер сегмента від 0, англійський текст, поточний український переклад і причину сумніву. Запропонована заміна бажана, але не обов’язкова. Додайте публічне джерело й зазначте невпевненість та використання машинного перекладу.

Виправлення українського перекладу має зберігати точні китайські й англійські поля, порядок сегментів та посилання з піньїнем. Якщо помилка в самому джерелі, запропонуйте окреме, явно позначене виправлення з текстом до та після зміни, доказами й новим хешем джерела. Не змінюйте оригінальний запис чи заморожені аудити. Якщо змінюється ієрогліф або читання, перевірте нову ідентичність і можливі дублікати; ID історичного батьківського запису не є дозволом автоматично замінити запис застосунку.

Новий кандидат потребує перевірки іншим рецензентом, прив’язаної до хешу всього кандидата. Зміна тексту робить попереднє схвалення застарілим. Зберігайте попередні пропозиції та відхилені висновки. Невирішене значення має залишатися відкладеним; часткове виправлення не кваліфікує весь запис.

Перевірка людиною фіксує точний показаний текст, рішення та межі компетенції. Перші три схвалення стосуються відповідності українських значень англійським; вони не підтверджують китайську мову чи загальну точність. Модельні висновки мають залишатися `human_validation: false` і `runtime_approved: false`. Поля історичної чернетки не змінюються. Чинні примітки старої чернетки містить лише `dictionary.json`; не домішуйте карантинні тексти чи старі черги.

Запускайте `python3 -B scripts/check_release.py` з повного checkout: він перевіряє інвентар файлів, заморожену чернетку, попередній overlay та новий випуск. `--status-only` перевіряє лише метадані. Не переписуйте очікувані хеші або заморожені валідатори заради проходження перевірки. Поточні показники та джерела містить [STATUS.json](STATUS.json).

Reports in English are welcome. Identify the release and source universe, exact Chinese/pinyin and source text, current Ukrainian, zero-based segment, reason, optional correction and public evidence. Distinguish a translation correction from a correction to CC-CEDICT itself. Use a separate source-bound candidate, retain history, and require a different reviewer's approval of its exact hash. Editing a candidate invalidates its old approval. A remaining unresolved segment keeps the complete candidate on hold.

Human review must record the exact displayed text and scope. English-to-Ukrainian gloss approval is separate from Chinese-language validation. Model work must not be labeled human reviewed. App admission requires a separate source/identity mapping audit; this release does not automatically replace runtime data.

Own contributions use [CC BY-SA 4.0](LICENSE). Credit compatible public sources. Do not include private data or unauthorized copies. External references are factual evidence, not permission to reproduce their prose or datasets. The existing issue templates and Git history remain available.
