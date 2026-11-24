# GIZA PRIME DUAL ATLAS 001 — архитектура и границы

Статус: реализовано в ветке `research/full-relational-math-reconstruction-001`
поверх HEAD `730f67cee244c7fe04f8a5253b57593706886a9`. PR #4 остаётся
OPEN / DRAFT / UNMERGED.

## 1. Два слоя в одном автономном HTML

`atlas_schematic.html` собирается `build_atlas_schematic.py` и содержит два
независимых встроенных документа:

| Идентификатор | Слой | Содержание |
| --- | --- | --- |
| `atlas-snapshot` | 01 RELATION SKELETON | 14 слотов, 9 семейств отношений, 0 реальных объектов и 0 связей. |
| `spatial-snapshot` | 02 SPATIAL 3D SKELETON | 41 контрольная точка GPMP, их метаданные и одна производная плоскость. |

Разделение snapshot'ов намеренное: relation-слой по-прежнему **не эмитирует
никаких координат** и помечен `SCHEMATIC / NOT GEODETIC`. Пространственный
слой содержит реальные значения, но помечен `SOURCE POINTS / NOT A TERRAIN MODEL`.

Переключение слоёв происходит без перезагрузки и без сетевых запросов.

## 2. Источник и разбор GPMP

Источник: `source_samples/GPMP-Control-Monuments.json` (точная копия локального
derived-массива). Верхний уровень содержит `source_file`, `sha256`, `kml_entry`,
`kml_bytes`, `folders`, `placemark_count`, `placemarks`.

`gpmp_spatial_layer.py` предоставляет явные функции:

- `parse_northing` — `Northing:` из описания;
- `parse_easting` — `Easting:` из описания;
- `parse_elevation` — `Elevation;` из описания;
- `parse_longitude_latitude` — `KML coordinates[0][0:2]` и отдельно Z;
- `classify_network` — `Description: Main|Secondary`;
- `validate_control_point` — полная проверка записи.

Контрольные значения **только для этого файла**: 41 точка, 11 `Main`, 30
`Secondary`, 41 уникальное имя. Диапазоны: Northing 98399.708–100154.421,
Easting 498718.109–500634.775, Elevation 19.570–197.555, Longitude
31.1209192–31.14077838, Latitude 29.96474083–29.98056996. Любое расхождение
вызывает `SpatialValidationError`, а не молчаливую подстановку.

### Критическое правило высот

Третье значение KML `coordinates` равно `0.0` у всех точек. Оно сохраняется как
`kml_z` с флагом `kml_z_is_elevation: false` и **никогда** не используется как
высота. Высота берётся только из `Elevation;` в исходном описании, которое
сохраняется полностью и без изменений.

### Система координат

Используется исходная ось `X = Easting`, `Y = Northing`, `Z = Elevation`.
`datum_status = unverified`. `conversion_to_epsg_wgs84` и
`helmert_spheroid_of_reference_transform` равны `not_performed`. Longitude и
latitude хранятся отдельными скалярными полями с
`relation_to_local_system = unresolved`. GPMP и ARCE Sphinx Grid не объединяются;
общего набора контрольных точек и проверенной матрицы преобразования нет.

## 3. Производная геометрия и идеализация

`spatial_geometry.py` — независимое ядро без внешних зависимостей: векторы,
центрирование, расстояния, углы, ортонормальная проверка базиса, вращения,
масштаб,минимальные квадраты, проекция на плоскость, интерполяция с оценкой
разброса, невязки и конструктор модели.

Все преобразования создают **новую** запись с `geometry_status =
DERIVED_GEOMETRY`; исходные координаты не перезаписываются.

В этом коммите вычислена одна производная плоскость по 41 точке. Её
`fit_residual.rms` около 24.2 исходных единиц — это честно показывает, что
одна плоскость **не** является рельефом и не должна использоваться как поверхность.

Идеализированные модели в этом коммите **не инстанцированы**
(`instantiated_models_in_this_commit = 0`): данных недостаточно для
валидированной поверхности пирамиды, Сфинкса или ландшафта. Архитектура требует
для каждой модели `model_id`, `model_type`, `source_ids`, `input_geometry_ids`,
`method`, `parameters`, `parameter_units`, `assumptions`, `fit_residual`,
`uncertainty`, `validity_domain`, `model_status`, `limitations`,
`falsification_conditions`. Статусы `IDEALIZED_MODEL`, `HYPOTHETICAL_MODEL`,
`MEASURED_GEOMETRY` и `UNKNOWN` не сливаются.

## 4. Интерактивность

Слой 02 реализует собственную 3D-проекцию на Canvas 2D без CDN и внешних
библиотек: вращение мышью, панорамирование, масштаб колесом, выбор точки,
паспорт точки, список с поиском и фильтрами Main/Secondary, подписи, графическая
сетка, вертикальное преувеличение (по умолчанию 1.0) и сброс вида. Управление
выполнено на `div` и `addEventListener`; inline-обработчиков, форм, таймеров и
сетевых вызовов нет.

Фигуры различаются не только цветом: Main — залитый круг, Secondary — ромб
(контур). Подписи и форма линий играют ту же роль.

## 5. Что НЕ является геометрией Гизы

- Точки GPMP — контрольная сеть, а не поверхность рельефа.
- Графическая сетка — опора координат, а не ландшафт.
- Положение узлов Relation Skeleton — экранная раскладка, а не география.
- Производная плоскость — аппроксимация контрольных точек, а не измеренная форма.
- Отсутствие геометрии не означает отсутствие объекта.

## 6. Проверки

- 58 исходных тестов инвентаря и атласа сохранены без изменений.
- Новые: `test_gpmp_spatial_layer.py`, `test_spatial_geometry.py`,
  `test_dual_atlas.py`.
- `python build_atlas_schematic.py` пересобирает HTML и
  `dual_atlas_import_report.json` детерминированно.
- Сборка прерывается при повреждённой структуре GPMP или падении honesty gate.
