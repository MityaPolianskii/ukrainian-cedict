# Як запропонувати виправлення / How to contribute

Почніть із [поточної редакторської черги](CURRENT_EDITORIAL_FOLLOWUP.json) або повідомте про іншу конкретну помилку. Перегляньте відкриті issues та [створіть issue за шаблоном](https://github.com/MityaPolianskii/ukrainian-cedict/issues/new/choose). Вкажіть ID, китайське слово, точний піньїнь, номер сегмента від 0, англійський текст, поточний український переклад і причину сумніву. Запропонована заміна бажана, але не обов’язкова. Додайте доступне публічне джерело й зазначте невпевненість та використання машинного перекладу.

Для PR зберігайте ID, китайські, англійські та джерельні поля, порядок сегментів, китайські посилання й піньїнь у дужках. Покажіть текст до та після зміни й пояснення. Виправлення мають отримати окремий overlay, синхронізовані CSV, поточні черги, лічильники й хеші. Поточний валідатор закріплює саме цей випуск: він не прийме зміненого словника без нового перевіреного baseline. Не змінюйте заморожені аудити чи очікувані хеші лише для проходження перевірки. Запускайте `python3 -B scripts/validate.py` на розпакованому ZIP без `.git`, щоб перевірити цей випуск.

Залишайте `human_validation: false` та `runtime_approved: false`. Критерії підтвердження перевірки людиною ще потрібно узгодити. Старі черги й карантинні примітки — історичні свідчення; чинні примітки містить лише `dictionary.json`.

Reports in English are welcome. Include the entry ID, exact Chinese/pinyin, zero-based segment index, English source, current Ukrainian text, reason, optional replacement and public supporting source. For PRs preserve source fields, IDs, segment order, references and bracketed pinyin. Explain before/after changes and any machine assistance. A new reviewed overlay and synchronized derived files are required for a future release. The current frozen validator verifies this exact release; do not rewrite immutable evidence or hashes merely to pass it.

Own contributions use [CC BY-SA 4.0](LICENSE). Credit compatible public sources. Do not include private data or unauthorized copies. The existing issue templates and Git history remain available.
