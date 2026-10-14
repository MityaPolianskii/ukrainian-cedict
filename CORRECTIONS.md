# Додаткове редакторське виправлення

## 2026-10-13: 發燒 / 发烧, `fa1 shao1`

**Автоматизоване виправлення чернетки, без людської валідації.** Виконано під час підготовки публічного пакета на підставі китайського слова, його точного читання та наявних англійських сегментів CC-CEDICT. Зовнішні словники для цього виправлення не перевірялися. Подальша перевірка людиною потрібна.

- ID: `63f73e7ccde6ccb2`
- `source_line`: 76380
- Джерело: CC-CEDICT, версія `2026-10-13T08:59:07Z`; атрибуція та контрольна сума повного джерела — у [source.json](source.json).
- Незмінений `raw_source`:

```text
發燒 发烧 [fa1 shao1] /to have a high temperature (from illness); to have a fever/(fig.) to be fascinated with; to obsess over/(fig.) flourishing; thriving; popular/
```

| Індекс від 0 | Англійський сегмент | Український текст до зміни | Український текст після зміни |
|---|---|---|---|
| 1 | (fig.) to be fascinated with; to obsess over | гарячка | (перен.) палко захоплюватися; бути одержимим чимось |
| 2 | (fig.) flourishing; thriving; popular | лічильні слова: 場\|场[chang2],次[ci4] | (перен.) бути в розквіті; процвітати; бути популярним |

Сегмент 0 залишено без змін: `мати високу температуру через хворобу; гарячкувати`.

### Причина та межі зміни

Кількість сегментів збігалася, але сегменти 1 і 2 не передавали відповідних переносних значень. Сегмент 2 містив сторонній перелік лічильних слів `場|场[chang2]` і `次[ci4]`, відсутніх у джерелі. Скрипт виявив цей збій посилань; семантичну невідповідність сегмента 1 встановлено окремо під час автоматизованого редакторського перегляду. Причину появи початкових перекладів не встановлено.

Заміни відновлюють підтримані джерелом переносні значення. Китайське написання, піньїнь, ID, джерельні поля, кількість і порядок сегментів не змінено. Початковий текст збережено вище, а сторонні посилання вилучено саме як частину обґрунтованої заміни невідповідного перекладу.

### Облік і результат перевірки

- `correction_count`: **0 → 2**.
- `model_reviewed: false`, `review_status: "not_model_reviewed"`, `review_rating_before_corrections: null`, `human_validation: false` залишено без змін. Ці поля стосуються історичної цільової перевірки.
- `translation_status: "model_generated"`, `has_known_uncertainty: false`, порожні `uncertainty_flags` і `uncertainty_notes` залишено без змін; це не гарантія правильності.
- Загальна кількість врахованих виправлень: **147 → 149 сегментів**, **129 → 130 записів**. Історичні 147 виправлень у 129 записах виділено окремо в `progress.json`.
- **5 596 записів, 15 435 пар сегментів, 704 історично перевірені моделлю записи, 27 позначених записів і 0 людських валідацій** не змінилися.
- JSON і CSV синхронізовано; контрольні суми оновлено. Повна локальна структурна перевірка проходить без помилок. Це не сертифікація мовної якості.

Цей журнал документує лише додаткове виправлення під час підготовки пакета. Він не реконструює історію попередніх 147 виправлень.


## 2026-10-14 expansion

All baseline records remain unchanged. New machine-draft corrections are recorded in EXPANSION_CORRECTIONS.json; original drafts are retained in the expansion working package. No human validation.


## 2026-10-14 second expansion

All 15,596 baseline records remain unchanged. New machine-draft corrections are recorded in EXPANSION2_CORRECTIONS.json; original outputs are retained in the expansion audit package. No human validation.


## 2026-10-14 third expansion

All 25,596 baseline records remain unchanged. New machine-draft corrections are recorded in EXPANSION3_CORRECTIONS.json; original outputs are retained in the expansion audit package. No human validation.


## 2026-10-14 fourth expansion

All 35,596 baseline records remain unchanged. New machine-draft corrections are recorded in EXPANSION4_CORRECTIONS.json; original outputs are retained in the expansion audit package. No human validation.


## 2026-10-14 fifth expansion

All 45,596 baseline records remain unchanged. New machine-draft corrections are recorded in EXPANSION5_CORRECTIONS.json; original outputs are retained in the expansion audit package. No human validation.


## 2026-10-14 sixth expansion

All 55,596 baseline records remain unchanged. New machine-draft corrections are recorded in EXPANSION6_CORRECTIONS.json; original outputs are retained in the expansion audit package. No human validation.
