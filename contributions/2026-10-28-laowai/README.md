# Переклади Laowai для розгляду · 28–29 жовтня 2026

Пропонуємо **3 186 переклади цілих словникових статей**, звірені з точним китайським написанням, піньїнем і всіма англійськими значеннями публічного CC-CEDICT від 23 жовтня 2026.

- **3 020** записів наразі відкладені в публічній версії словника.
- **166** — альтернативи до вже кваліфікованих перекладів. Поточні варіанти не перезаписано.
- Нової людської валідації немає. `human_validation` і `runtime_approved` залишаються `false`.

Це окремий внесок для розгляду, а не автоматична заміна чинного випуску, його статистики чи даних застосунку. Вихідні дані, попередні рішення та заморожені випуски збережені.

## Файли

- `dictionary.json.gz` / `reviewed-additions.json.gz`: повні тексти, вихідні англійські сегменти, походження, рішення та контрольні суми перекладів.
- `dictionary.csv.gz`: табличне подання тих самих текстів.
- `reviewed-additions.xml.gz`: XML-подання всіх пропозицій без втрати тексту.
- `manifest.json`: точні SHA-256 та розміри файлів.

Переклади мають `translation_alignment: whole_record`. Вони **не** є штучно розбитими сегментами, вирівняними один до одного з кожним англійським значенням. Для інтеграції в сегментний формат проєкту потрібен окремий редакційний крок; розділяти текст за крапкою з комою автоматично не можна.

## Як зроблено і перевірено

Чернетки переважно створено GPT-6.1 Terra з effort xhigh. Інший ШІ-агент читав китайський заголовок, точне читання, повний англійський текст і українську пропозицію; джерельні неточності та конкретну невпевненість записано окремо. Остаточні адресні виправлення також перевіряв головний агент Codex. Вказані моделі не є незалежною атестацією фактичного бекенду.

Перед публічною проєкцією виробничий перевіряльник прочитав справжні ланцюжки джерела, чернетки й останнього рішення за SHA-256. Непідтверджені, нерозв’язані та незіставлені з публічним джерелом записи до внеску не ввійшли. Контрольні суми початкових рішень і текстів збережено в записах. Публічний валідатор перевіряє цілісність, точну джерельну ідентичність, підрахунки та рівність JSON/CSV/XML; він не повторює мовну рецензію і не засвідчує особу рецензента.

Показники цієї ШІ-перевірки не є оцінкою точності, людським схваленням чи дозволом на автоматичне використання в застосунку. Історичні три людські схвалення іншого випуску цим внеском не розширюються. Текстів прикладів, аудіо, списків HSK, внутрішніх ID застосунку чи даних користувача тут немає.

## Перевірка з кореня репозиторію

```sh
python3 -B contributions/2026-10-28-laowai/validate.py contributions/2026-10-28-laowai source-updates/2026-10-25/source-records.json.gz
python3 -B scripts/check_release.py
```

Походження: CC-CEDICT, учасники CC-CEDICT, MDBG, засновник CEDICT Paul Andrew Denisowski. Українські адаптації: Laowai / Dmytro Polianskyi, збережені відомості про джерело. Дані поширюються за [CC BY-SA 4.0](../../LICENSE), як і власні внески цього проєкту. Новий валідатор цього внеску — оригінальний код Laowai, під MIT (`VALIDATOR-LICENSE`).

---

## English summary

3,186 source-bound record-level Ukrainian translation proposals: 3,020 for currently held exact-upstream records and 166 alternatives to existing qualified translations. The current 122,291-record release and all frozen history remain unchanged. Drafting primarily used GPT-6.1 Terra xhigh; different-agent semantic review and source/draft/final-target integrity checks were performed. New human validation is zero and runtime approval remains false. Model metadata is not independently attested and model review is not a measured accuracy percentage.

JSON, CSV and XML contain the same complete record-level glosses; they are not falsely labelled as one-to-one sense segmentation. Unresolved or source-mismatched items are excluded. Integration into the existing per-sense release remains a separate editorial step. Original upstream contributors and licence are retained.
