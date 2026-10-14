# Як запропонувати виправлення

Якщо знаєте китайську й українську, допоможіть перевірити переклади. Можна почати зі 194 записів із позначеними сумнівами або з [виправлення 發燒 / 发烧](CORRECTIONS.md). Помилки можуть бути й в інших записах.

## Повідомити про помилку

Перевірте [відкриті issues](https://github.com/MityaPolianskii/ukrainian-cedict/issues), а потім [створіть нове](https://github.com/MityaPolianskii/ukrainian-cedict/issues/new/choose) за відповідним шаблоном. Вкажіть:

- ID запису, китайське слово та точний піньїнь.
- Номер сегмента, починаючи з 0, його англійський текст і наявний український переклад.
- Що саме неправильно: значення, читання, стиль, термін чи щось інше.
- Запропоновану заміну, якщо маєте її, та пояснення. Додайте публічне посилання на джерело, якщо воно допоможе, і зазначте сумніви.

Готовий переклад не обов’язковий: достатньо описати конкретну проблему. Для нового запису наведіть публічний рядок CC-CEDICT та версію джерела. Зміну самої версії джерела слід обговорити окремо.

## Надіслати pull request

Для виправлення перекладу:

1. Змінюйте український текст, зберігаючи ID, китайське написання, піньїнь, джерельний рядок та англійські сегменти. Якщо помилка, на вашу думку, є в CC-CEDICT, повідомте про неї окремо.
2. Збережіть кількість і порядок сегментів, китайські посилання та піньїнь у квадратних дужках. Не видаляйте посилання заради проходження перевірки. Обґрунтований приклад заміни помилкового тексту є в [CORRECTIONS.md](CORRECTIONS.md).
3. Оновіть JSON і відповідний рядок CSV. Масиви в CSV залишайте JSON-масивами, булеві значення — `true` / `false`, порожню оцінку — порожнім полем.
4. Оновіть потрібні лічильники й контрольні суми даних у `progress.json`, а також контрольні суми змінених файлів у `SHA256SUMS.txt`.
5. Запустіть `python3 scripts/validate.py`. В описі PR покажіть текст до й після зміни, поясніть причину, наведіть джерела та результат скрипту.

`correction_count` рахує виправлені сегменти. Зміна документації або повторний перегляд незміненого перекладу не збільшує цей лічильник. Нові виправлення обліковуйте окремо від історичних 147 сегментів у 129 записах у `correction_breakdown`.

Залишайте `human_validation: false`. Для позначення перевірки людиною ще потрібно узгодити критерії та спосіб підтвердження її обсягу; поточний скрипт очікує `false`. В описі внеску вкажіть, що саме ви перевірили та чи використовували машинний переклад.

## Джерела та ліцензія

Власні внески надаються за [CC BY-SA 4.0](LICENSE). Для чужих матеріалів перевірте сумісність ліцензії та вкажіть джерело. Зазвичай достатньо посилання й власного пояснення; не копіюйте великі фрагменти словників або підручників. Не додавайте приватні дані, облікові відомості чи закриті журнали.

## English

To report an error, check existing issues and open one using a template. Include the entry ID, Chinese headword, exact pinyin, segment index (starting at 0), English segment, current Ukrainian text, and what is wrong. A replacement is welcome but optional. Explain your reasoning, link useful public sources, and mention uncertainty.

For a translation PR, preserve the source fields, IDs, segment order and count, Chinese references, and bracketed pinyin. Keep JSON and CSV in sync; update the relevant counts and hashes in `progress.json` and `SHA256SUMS.txt`. Run `python3 scripts/validate.py` and include its output, the old and new text, and your reasoning in the PR. Keep new corrections separate from the historical counts and leave `human_validation: false`. State what you checked and whether you used machine translation.

Contribute your own wording or material with a compatible licence. Contributions use [CC BY-SA 4.0](LICENSE); credit sources and identify changes. Do not include private data or unauthorised copies of other dictionaries.
