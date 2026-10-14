# Ukrainian CEDICT — китайсько-український словник

Це китайсько-український словник у форматах JSON і CSV. Китайське написання, піньїнь і англійські пояснення взято з [CC-CEDICT](https://www.mdbg.net/chinese/dictionary?page=cc-cedict); український текст додала модель.

**Це чернетка. Люди ще не перевіряли українські переклади.** Помилки можливі й у записах без попереджень. Перед використанням у навчальних матеріалах чи застосунку перевірте потрібні записи.

Приклад із файлу: 學習 / 学习 (`xue2 xi2`) — «вчитися; навчатися».

## Завантажити

| Файл | Що всередині |
|---|---|
| [JSON](https://raw.githubusercontent.com/MityaPolianskii/ukrainian-cedict/main/dictionary.json) | Усі записи: слова, переклади, джерельний текст і позначки перевірки |
| [CSV](https://raw.githubusercontent.com/MityaPolianskii/ukrainian-cedict/main/dictionary.csv) | Ті самі дані для роботи в таблицях; UTF-8 з BOM, списки збережено як JSON |
| [Весь репозиторій ZIP](https://github.com/MityaPolianskii/ukrainian-cedict/archive/refs/heads/main.zip) | Дані, документація та скрипт перевірки |

Імпортуйте колонки CSV як текст, щоб редактор не змінив піньїнь чи інші значення. Окремо доступні [лічильники й контрольні суми](progress.json), [відомості про джерело](source.json) та [інструкція перекладу](translation_prompt.txt).

## Що вже зроблено

Стан на 14 жовтня 2026 року:

| Показник | Кількість |
|---|---:|
| Словникові записи | 35 596 |
| Пари англійських та українських сегментів | 61 620 |
| Записи, перевірені іншою моделлю | 704 |
| Виправлені сегменти | 309 у 245 записах |
| Записи з позначеними сумнівами | 457 |
| Записи, перевірені людьми | 0 |

Усі опубліковані записи мають український текст. Це 28,42% від 125 264 записів у зафіксованій версії CC-CEDICT; решта джерела сюди не входить.

Записи для перевірки іншою моделлю добирали окремо. За результатами цієї перевірки не можна оцінити точність усього словника. Позначені сумніви теж не охоплюють усіх можливих помилок.

Після тієї перевірки виправлено 147 сегментів у 129 записах. Під час підготовки публікації автоматично виправлено ще два сегменти в 發燒 / 发烧 (`fa1 shao1`). Текст до й після зміни та причини наведено в [CORRECTIONS.md](CORRECTIONS.md). Цей запис не додано до 704 перевірених іншою моделлю записів; він також потребує перевірки людиною.

## Розширення від 14 жовтня 2026 року

Додано 10 000 нових машинно перекладених записів. Усі 5 596 попередніх записів та їхні метадані перевірки збережено без змін. Нові записи не проходили повної мовної перевірки; 106 із них вибірково перевірено на значення. Це не є повною перевіркою за попереднім протоколом, оцінкою загальної точності чи людською валідацією.

- [Журнал виправлень](EXPANSION_CORRECTIONS.json) — текст до й після змін.
- [Черга перевірки](EXPANSION_REVIEW_QUEUE.json) — 167 нових записів із відомими застереженнями.
- [Структурна перевірка та звірка джерела](EXPANSION_VALIDATION.json) — результат перевірки розширення.
- [Вибіркова перевірка значень](EXPANSION_SEMANTIC_CHECK.json) — її обсяг, знахідки та обмеження.

## Друге розширення від 14 жовтня 2026 року

Додано ще 10 000 машинно перекладених записів (15 438 пар сегментів). Усі 15 596 попередніх записів, їхні переклади, виправлення та метадані перевірки збережено без змін. Вибірково перевірено значення 300 нових записів; це не повна мовна перевірка, не оцінка загальної точності й не людська валідація.

- [Нові виправлення](EXPANSION2_CORRECTIONS.json) — текст до й після змін.
- [Нова черга перевірки](EXPANSION2_REVIEW_QUEUE.json) — 94 записів із застереженнями.
- [Структурна перевірка та звірка джерела](EXPANSION2_VALIDATION.json).
- [Вибіркова перевірка значень](EXPANSION2_SEMANTIC_CHECK.json).

## Третє розширення від 14 жовтня 2026 року

Додано ще 10 000 машинно перекладених записів (15 261 пар сегментів). Усі 25 596 попередніх записів, їхні переклади, виправлення та метадані перевірки збережено без змін. Вибірково перевірено значення 300 нових записів; це не повна мовна перевірка, не оцінка загальної точності й не людська валідація.

- [Нові виправлення](EXPANSION3_CORRECTIONS.json) — текст до й після змін.
- [Нова черга перевірки](EXPANSION3_REVIEW_QUEUE.json) — 169 записів із застереженнями.
- [Структурна перевірка та звірка джерела](EXPANSION3_VALIDATION.json).
- [Вибіркова перевірка значень](EXPANSION3_SEMANTIC_CHECK.json).

## Знайшли помилку?

[Відкрийте issue](https://github.com/MityaPolianskii/ukrainian-cedict/issues/new/choose). Вкажіть китайське слово, піньїнь, ID запису й номер сегмента, починаючи з 0. Покажіть наявний переклад і поясніть, що з ним не так. Запропонуйте заміну, якщо маєте її.

Як подати виправлення або PR, описано в [CONTRIBUTING.md](CONTRIBUTING.md). Можна почати з 457 позначених записів або з виправлення 發燒, описаного вище.

## Перевірити файли

Потрібен Python 3.9 або новіший, без додаткових бібліотек і доступу до мережі:

```sh
python3 scripts/validate.py
```

У Windows можна використати `py -3 scripts/validate.py`. Скрипт перевіряє формат, ID, порядок записів, відповідність сегментів, китайські посилання й текст у квадратних дужках, узгодженість JSON та CSV, лічильники й контрольні суми.

Успішна перевірка означає, що файли узгоджені між собою. Скрипт не оцінює переклади й не звіряє дані із зовнішнім CC-CEDICT.

<details>
<summary>Формат записів і налаштування перекладу</summary>

Один запис — це традиційне й спрощене написання з точним піньїнем. Для різних читань можуть бути окремі записи.

- `traditional`, `simplified`, `pinyin`, `raw_source`, `source_line` — поля джерела та номер його рядка. Записи впорядковано за `source_line`.
- `english_segments`, `ukrainian_segments` — відповідні списки з однаковою кількістю елементів. Межі взято з розділювача `/` у CC-CEDICT Version 1; вони не завжди відділяють різні значення.
- `id` — перші 16 шістнадцяткових символів SHA-256 від `traditional + TAB + simplified + TAB + pinyin` у UTF-8. Регістр, пробіли, тони та `u:` мають значення.
- `translation_status` — завжди `model_generated`. `model_reviewed` і `review_status` позначають перевірку іншою моделлю, а `review_rating_before_corrections` — її оцінку до виправлень.
- `correction_count` — кількість врахованих виправлених сегментів. `has_known_uncertainty`, `uncertainty_flags`, `uncertainty_notes` — відомі сумніви.
- `human_validation` — завжди `false` у цій версії.

Китайські посилання й піньїнь у квадратних дужках потрібно зберігати дослівно у відповідному українському сегменті.

Модель отримала інструкцію враховувати китайське слово та його читання й зберігати відповідність англійських і українських сегментів. У [progress.json](progress.json) записано запитані налаштування; фактична модель і витрата токенів невідомі.

Валідатор повертає `0`, якщо перевірки пройдено, `1`, якщо знайдено помилки, і `2`, якщо не вдалося прочитати файли або параметри. Для іншого розташування даних передайте `--root /шлях/до/репозиторію`.

</details>

## Джерело та ліцензія

CC-CEDICT створюють його учасники, публікує MDBG. Він походить від CEDICT, започаткованого Paul Andrew Denisowski. Тут використано версію від **2026-10-13 08:59:07 UTC**; відбір записів, українські переклади та позначки перевірки — зміни цього проєкту. Відомості про джерело та його контрольна сума — у [source.json](source.json).

Дані, українські переклади, документація, шаблони issues та скрипт поширюються за [CC BY-SA 4.0](LICENSE). Зберігайте атрибуцію та посилання на ліцензію, зазначайте зміни й поширюйте адаптації за тією самою ліцензією. [Повні умови](https://creativecommons.org/licenses/by-sa/4.0/legalcode.en) мають пріоритет. Проєкт не заявляє про схвалення з боку MDBG чи учасників CC-CEDICT.

## English

Ukrainian CEDICT contains Chinese headwords, pinyin, English definitions from CC-CEDICT, and Ukrainian translations generated by a model. The translations have not been reviewed by people. Unflagged entries may still contain errors.

The current draft has 35,596 entries and 61,620 aligned segments. Another model reviewed 704 selected entries; this does not measure overall accuracy. There are 309 corrected segments across 245 entries, 457 entries with known concerns, and zero human-validated entries. This covers 28.42% of the pinned CC-CEDICT source.

On 14 October 2026, 10,000 machine-draft entries were added, preserving all 5,596 baseline entries and their review metadata. A targeted semantic spot check covered 106 new entries; it is not a full review under the earlier protocol or an accuracy estimate. See the [correction log](EXPANSION_CORRECTIONS.json), [review queue](EXPANSION_REVIEW_QUEUE.json), [validation record](EXPANSION_VALIDATION.json), and [semantic spot-check report](EXPANSION_SEMANTIC_CHECK.json).

A second expansion on 14 October 2026 added another 10,000 machine-draft entries and 15,438 aligned segments. All 15,596 previous entries and their review metadata remain unchanged. A targeted semantic sample covered 300 new entries, without full linguistic or human validation. See the [new correction log](EXPANSION2_CORRECTIONS.json), [review queue](EXPANSION2_REVIEW_QUEUE.json), [source validation](EXPANSION2_VALIDATION.json), and [semantic check](EXPANSION2_SEMANTIC_CHECK.json).

A third expansion on 14 October 2026 added another 10,000 machine-draft entries and 15,261 aligned segments. All 25,596 previous entries and their review metadata remain unchanged. A targeted semantic sample covered 300 new entries, without full linguistic or human validation. See the [new correction log](EXPANSION3_CORRECTIONS.json), [review queue](EXPANSION3_REVIEW_QUEUE.json), [source validation](EXPANSION3_VALIDATION.json), and [semantic check](EXPANSION3_SEMANTIC_CHECK.json).

Download [JSON](https://raw.githubusercontent.com/MityaPolianskii/ukrainian-cedict/main/dictionary.json), [CSV](https://raw.githubusercontent.com/MityaPolianskii/ukrainian-cedict/main/dictionary.csv), or the [repository ZIP](https://github.com/MityaPolianskii/ukrainian-cedict/archive/refs/heads/main.zip). To report an error, open an issue with the entry ID, headword, exact pinyin, segment index (starting at 0), current translation, and your explanation. See the [English contribution guide](CONTRIBUTING.md#english).

Source credit: CC-CEDICT contributors, published by MDBG, based on CEDICT by Paul Andrew Denisowski. Data and project materials use [CC BY-SA 4.0](LICENSE): retain attribution, link the licence, identify changes, and share adaptations under the same licence.
