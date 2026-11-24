import re
from collections import defaultdict
from datetime import timezone, datetime, timedelta, tzinfo
from pathlib import PurePosixPath
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydriller import Commit, ModificationType



def _get_timezone(timezone_name: str):
    """Возвращает ZoneInfo, а на Windows без пакета tzdata — фиксированный сдвиг."""
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        fallback_offsets = {
            "Asia/Yekaterinburg": timezone(timedelta(hours=5)),
            "Europe/Moscow": timezone(timedelta(hours=3)),
            "UTC": timezone.utc,
        }
        return fallback_offsets.get(timezone_name, timezone(timedelta(hours=5)))

# Стоп-слова и шаблонные фразы, по которым непонятно, что именно изменилось
GENERIC_MESSAGES = {
    "fix", "fixes", "fixed", "bug", "bugfix", "fix bug", "fix bugs",
    "update", "updates", "updated", "upd",
    "change", "changes", "changed",
    "work", "wip", "test", "testing", "temp", "tmp",
    "commit", "initial commit", "first commit",
    "done", "ready", "ok", "some changes", "minor changes",
    "фикс", "исправление", "исправил", "правки", "обновление", "обновил",
    "тест", "готово", "изменения", "мелкие правки", "коммит",
}

# Регулярка для проверки формата Conventional Commits (например: "feat(api): add login")
CONVENTIONAL_PATTERN = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-zA-Z0-9_-]+\))?:\s+.{4,}"
)


# Категории мусорных директорий и файлов, которым не место в Git
REPO_JUNK_RULES: dict[str, dict[str, set[str]]] = {
    "dependencies": {
        "dirs": {"node_modules", "bower_components", "vendor", ".pnp"},
        "files": set(),
        "extensions": set(),
    },
    "virtual_envs": {
        "dirs": {"venv", ".venv", "env", ".env_venv", "virtualenv"},
        "files": set(),
        "extensions": set(),
    },
    "cache_and_build": {
        "dirs": {
            "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
            ".next", ".nuxt", "dist", "build", ".gradle", "target", ".parcel-cache",
        },
        "files": {".eslintcache", ".tsbuildinfo"},
        "extensions": {".pyc", ".pyo", ".pyd", ".class", ".o", ".obj", ".log"},
    },
    "os_and_ide": {
        "dirs": {".idea", ".vscode", ".vs", "__MACOSX"},
        "files": {".DS_Store", "Thumbs.db", "desktop.ini"},
        "extensions": {".swp", ".swo", ".tmp", ".bak"},
    },
    "secrets": {
        "dirs": set(),
        "files": {".env", ".env.local", ".env.production", ".env.development"},
        "extensions": {".pem", ".key"},
    },
}

def _classify_junk_path(file_path: str) -> str | None:
    """
    Проверяет путь файла на попадание под правила мусорных файлов.
    Возвращает название категории нарушения или None, если файл нормальный.
    """
    normalized = file_path.replace("\\", "/")
    path_obj = PurePosixPath(normalized)

    parts_lower = {part.lower() for part in path_obj.parts[:-1]}
    filename_lower = path_obj.name.lower()
    suffix_lower = path_obj.suffix.lower()

    for category, rules in REPO_JUNK_RULES.items():
        # 1. Проверка на запрещенные папки в пути (например, node_modules/... или .idea/...)
        if any(d.lower() in parts_lower for d in rules["dirs"]):
            return category

        # 2. Проверка на точное совпадение имени файла (например, .DS_Store, .env)
        if any(f.lower() == filename_lower for f in rules["files"]):
            return category

        # 3. Проверка на запрещенные расширения (например, .pyc, .log)
        if suffix_lower in rules["extensions"]:
            return category

    return None


def calculate_repository_cleanliness(commits: list[Commit]) -> dict:
    """
    Метрика №6: Чистота репозитория.
    Проверяет, попадали ли в коммиты за спринт зависимости, виртуальные окружения,
    кэш, системные файлы или секреты.
    """
    total_commits = 0
    dirty_commits_count = 0
    violations_by_category: dict[str, int] = {cat: 0 for cat in REPO_JUNK_RULES}
    dirty_examples = []
    seen_dirty_paths: set[str] = set()

    for commit in commits:
        if commit.merge:
            continue

        total_commits += 1
        commit_has_junk = False

        for mod_file in commit.modified_files:
            # Если файл удаляют (чистят репозиторий), это не нарушение
            if mod_file.change_type == ModificationType.DELETE:
                continue

            file_path = mod_file.new_path or mod_file.old_path
            if not file_path:
                continue

            category = _classify_junk_path(file_path)
            if category:
                commit_has_junk = True
                violations_by_category[category] += 1

                # Сохраняем до 15 уникальных примеров для отчета
                if file_path not in seen_dirty_paths and len(dirty_examples) < 15:
                    seen_dirty_paths.add(file_path)
                    dirty_examples.append({
                        "hash": commit.hash[:7],
                        "author": commit.author.email or commit.author.name,
                        "file_path": file_path,
                        "category": category,
                    })

        if commit_has_junk:
            dirty_commits_count += 1

    clean_commits_count = total_commits - dirty_commits_count
    cleanliness_percent = (
        round((clean_commits_count / total_commits) * 100, 2)
        if total_commits > 0
        else 100.0
    )

    return {
        "is_clean": dirty_commits_count == 0,
        "cleanliness_percent": cleanliness_percent,
        "total_checked_commits": total_commits,
        "dirty_commits_count": dirty_commits_count,
        "violations_by_category": {
            k: v for k, v in violations_by_category.items() if v > 0
        },
        "dirty_examples": dirty_examples,
    }



def _is_commit_message_meaningful(message: str) -> tuple[bool, str | None]:
    """
    Проверяет осмысленность сообщения коммита.
    Возвращает (True, None), если сообщение хорошее,
    или (False, "причина"), если сообщение плохое.
    """
    # Берем только первую строку (заголовок коммита)
    subject = message.strip().splitlines()[0].strip() if message.strip() else ""

    if not subject:
        return False, "Пустое сообщение"

    # 1. Только цифры или знаки препинания (например, "123", "...")
    if not re.search(r"[a-zA-Zа-яА-ЯёЁ]", subject):
        return False, "Не содержит слов (только цифры или символы)"

    # 2. Повторяющиеся символы (например, "аааа", "qqqq")
    if len(set(subject.lower().replace(" ", ""))) <= 2:
        return False, "Набор повторяющихся символов"

    # Очищаем строку от лишних символов для проверки по словарю и словам
    cleaned = re.sub(r"[^\w\sа-яА-ЯёЁ-]", "", subject.lower()).strip()

    # 3. Проверка на стоп-фразы ("fix bug", "update", "правки")
    if cleaned in GENERIC_MESSAGES:
        return False, "Слишком общая формулировка"

    # 4. Проверка минимальной длины и количества слов
    words = [w for w in cleaned.split() if len(w) > 1]
    if len(subject) < 10 or len(words) < 2:
        return False, "Слишком короткое сообщение (меньше 2 осмысленных слов)"

    return True, None


def calculate_commit_messages_quality(commits: list[Commit]) -> dict:
    """
    Метрика №3: Качество сообщений коммитов.
    Возвращает долю информативных коммитов и список проблемных примеров для разбора.
    """
    total_evaluated = 0
    meaningful_count = 0
    conventional_count = 0
    bad_examples = []

    for commit in commits:
        # Игнорируем автоматические merge-коммиты
        if commit.merge:
            continue

        total_evaluated += 1
        subject = commit.msg.strip().splitlines()[0].strip() if commit.msg.strip() else ""

        if CONVENTIONAL_PATTERN.match(subject):
            conventional_count += 1

        is_good, reason = _is_commit_message_meaningful(commit.msg)
        if is_good:
            meaningful_count += 1
        else:
            # Сохраняем до 10 примеров плохих коммитов, чтобы показать их в отчете команды
            if len(bad_examples) < 10:
                bad_examples.append({
                    "hash": commit.hash[:7],
                    "author": commit.author.email or commit.author.name,
                    "message": subject,
                    "reason": reason,
                })

    quality_share = (
        round((meaningful_count / total_evaluated) * 100, 2)
        if total_evaluated > 0
        else 100.0
    )

    return {
        "total_evaluated_commits": total_evaluated,
        "meaningful_commits": meaningful_count,
        "quality_percent": quality_share,
        "conventional_commits_count": conventional_count,
        "bad_examples": bad_examples,
    }




def calculate_changes_volume_distribution(commits: list[Commit]) -> dict:
    """
    Метрика №2: Распределение объёма изменений (доля изменённых символов по авторам за спринт).
    Возвращает данные, готовые для отрисовки круговой диаграммы на фронтенде.
    """
    chars_by_author: dict[str, int] = defaultdict(int)
    total_chars = 0

    for commit in commits:
        # Пропускаем merge-коммиты, чтобы не дублировать чужие изменения при слиянии веток
        if commit.merge:
            continue

        # Используем email как уникальный идентификатор автора (или commit.author.name)
        author_key = commit.author.email
        commit_chars = 0

        for mod_file in commit.modified_files:
            # Пропускаем бинарные файлы (картинки, архивы, скомпилированные файлы),
            # у них diff_parsed пустой или не несет текстового кода
            if not mod_file.diff_parsed:
                continue

            added_lines = mod_file.diff_parsed.get("added", [])
            deleted_lines = mod_file.diff_parsed.get("deleted", [])

            # Считаем количество непробельных символов в добавленных и удалённых строках
            added_chars = sum(len(line_text.strip()) for _, line_text in added_lines)
            deleted_chars = sum(len(line_text.strip()) for _, line_text in deleted_lines)

            commit_chars += added_chars + deleted_chars

        chars_by_author[author_key] += commit_chars
        total_chars += commit_chars

    # Формируем итоговое распределение с долями в процентах для круговой диаграммы
    distribution = []
    for author, chars in sorted(chars_by_author.items(), key=lambda x: x[1], reverse=True):
        share_percent = round((chars / total_chars) * 100, 2) if total_chars > 0 else 0.0
        distribution.append({
            "author": author,
            "changed_chars": chars,
            "share_percent": share_percent,
        })

    return {
        "total_changed_chars": total_chars,
        "authors": distribution,
    }




WEEKDAYS_RU = [
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье",
]


def calculate_work_regularity(
    commits: list[Commit],
    timezone_name: str = "Asia/Yekaterinburg",
    sprint_days: int | None = None,
) -> dict:
    """
    Метрика №4: Регулярность работы (тепловая карта активности).
    Группирует коммиты по дням недели, часам и календарным датам,
    а также вычисляет коэффициент равномерности распределения работы.
    """
    target_tz = _get_timezone(timezone_name)

    # Счётчики по дням недели (0 = Пн ... 6 = Вс)
    commits_by_weekday = [0] * 7
    # Матрица 7x24 для детальной тепловой карты (день недели -> час 0..23)
    heatmap_matrix = [[0 for _ in range(24)] for _ in range(7)]
    # Активность по конкретным календарным датам ("YYYY-MM-DD" -> кол-во коммитов)
    commits_by_date: dict[str, int] = defaultdict(int)

    total_commits = 0

    for commit in commits:
        if commit.merge:
            continue

        total_commits += 1

        # Приводим дату коммита к согласованному часовому поясу команды
        dt = commit.author_date
        if dt.tzinfo is not None:
            dt_local = dt.astimezone(target_tz)
        else:
            dt_local = dt.replace(tzinfo=target_tz)

        weekday_idx = dt_local.weekday()  # 0..6
        hour = dt_local.hour              # 0..23
        date_str = dt_local.strftime("%Y-%m-%d")

        commits_by_weekday[weekday_idx] += 1
        heatmap_matrix[weekday_idx][hour] += 1
        commits_by_date[date_str] += 1

    # Формируем удобный список по дням недели для графика на фронтенде
    by_weekday_list = []
    for idx, day_name in enumerate(WEEKDAYS_RU):
        count = commits_by_weekday[idx]
        share = round((count / total_commits) * 100, 2) if total_commits > 0 else 0.0
        by_weekday_list.append({
            "day_index": idx,
            "day_name": day_name,
            "commits_count": count,
            "share_percent": share,
        })

    # Список точек для 2D тепловой карты [день_недели, час, количество] (стандартный формат ECharts)
    heatmap_points = []
    for day_idx in range(7):
        for hour in range(24):
            count = heatmap_matrix[day_idx][hour]
            if count > 0:
                heatmap_points.append({
                    "day_index": day_idx,
                    "day_name": WEEKDAYS_RU[day_idx],
                    "hour": hour,
                    "commits_count": count,
                })

    # Сортируем календарные даты по возрастанию
    daily_timeline = [
        {"date": d, "commits_count": commits_by_date[d]}
        for d in sorted(commits_by_date.keys())
    ]

    # Коэффициент регулярности: отношение активных дней к длительности периода (по умолчанию 7 дней)
    active_days_count = len(commits_by_date) if sprint_days else sum(1 for c in commits_by_weekday if c > 0)
    denominator = sprint_days if (sprint_days and sprint_days > 0) else 7
    regularity_coefficient = round(min(active_days_count / denominator, 1.0), 2)

    # Находим пиковый день недели
    peak_day = max(by_weekday_list, key=lambda x: x["commits_count"]) if total_commits > 0 else None

    return {
        "timezone": timezone_name,
        "total_commits": total_commits,
        "active_days_count": active_days_count,
        "regularity_coefficient": regularity_coefficient,
        "peak_weekday": peak_day["day_name"] if peak_day else None,
        "by_weekday": by_weekday_list,
        "daily_timeline": daily_timeline,
        "heatmap_2d": heatmap_points,
    }



def _ensure_aware_dt(dt: datetime, default_tz: tzinfo) -> datetime:
    """Гарантирует, что у datetime есть часовой пояс (aware)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=default_tz)
    return dt


def calculate_deadline_activity(
    commits: list[Commit],
    deadline: datetime | None,
    timezone_name: str = "Asia/Yekaterinburg",
    last_hours_window: int = 24,
) -> dict:
    """
    Метрика №8: Активность перед дедлайном.
    Считает:
    1) долю коммитов, сделанных в последние `last_hours_window` часов (и 6 часов) до дедлайна;
    2) распределение активности по времени суток в согласованном часовом поясе:
       - дневное/рабочее окно: 09:00 – 23:00
       - ночной аврал: 03:00 – 06:00
    """
    team_tz = _get_timezone(timezone_name)

    deadline_utc: datetime | None = None
    if deadline is not None:
        deadline_aware = _ensure_aware_dt(deadline, team_tz)
        deadline_utc = deadline_aware.astimezone(timezone.utc)

    total_commits = 0
    daytime_commits = 0      # 09:00 <= hour < 23:00
    night_rush_commits = 0   # 03:00 <= hour < 06:00
    other_hours_commits = 0  # 23:00 – 03:00 и 06:00 – 09:00

    last_24h_commits = 0
    last_6h_commits = 0
    hours_before_deadline_list: list[float] = []

    for commit in commits:
        if commit.merge:
            continue

        total_commits += 1

        # 1. Приводим дату коммита к согласованному часовому поясу команды
        commit_aware = _ensure_aware_dt(commit.author_date, team_tz)
        commit_team_dt = commit_aware.astimezone(team_tz)
        hour = commit_team_dt.hour

        if 9 <= hour < 23:
            daytime_commits += 1
        elif 3 <= hour < 6:
            night_rush_commits += 1
        else:
            other_hours_commits += 1

        # 2. Если передан дедлайн, считаем точный остаток времени в едином UTC
        if deadline_utc is not None:
            commit_utc = commit_aware.astimezone(timezone.utc)
            hours_left = (deadline_utc - commit_utc).total_seconds() / 3600

            # Учитываем коммиты, сделанные до дедлайна (включая небольшой допуск 0 ч)
            if hours_left >= 0:
                hours_before_deadline_list.append(round(hours_left, 2))
                if hours_left <= last_hours_window:
                    last_24h_commits += 1
                if hours_left <= 6:
                    last_6h_commits += 1

    daytime_share = round((daytime_commits / total_commits) * 100, 2) if total_commits > 0 else 0.0
    night_rush_share = round((night_rush_commits / total_commits) * 100, 2) if total_commits > 0 else 0.0

    deadline_stats = None
    if deadline_utc is not None:
        last_24h_share = round((last_24h_commits / total_commits) * 100, 2) if total_commits > 0 else 0.0
        last_6h_share = round((last_6h_commits / total_commits) * 100, 2) if total_commits > 0 else 0.0
        avg_hours_before = (
            round(sum(hours_before_deadline_list) / len(hours_before_deadline_list), 2)
            if hours_before_deadline_list
            else None
        )
        min_hours_before = min(hours_before_deadline_list) if hours_before_deadline_list else None

        deadline_stats = {
            "deadline_team_tz": deadline_utc.astimezone(team_tz).isoformat(),
            "last_24h_commits": last_24h_commits,
            "last_24h_share_percent": last_24h_share,
            "last_6h_commits": last_6h_commits,
            "last_6h_share_percent": last_6h_share,
            "avg_hours_before_deadline": avg_hours_before,
            "closest_commit_hours_before_deadline": min_hours_before,
        }

    return {
        "timezone": timezone_name,
        "total_commits": total_commits,
        "time_windows": {
            "daytime_09_23": {
                "commits_count": daytime_commits,
                "share_percent": daytime_share,
            },
            "night_rush_03_06": {
                "commits_count": night_rush_commits,
                "share_percent": night_rush_share,
            },
            "other_hours": {
                "commits_count": other_hours_commits,
                "share_percent": round(100.0 - daytime_share - night_rush_share, 2) if total_commits > 0 else 0.0,
            },
        },
        "deadline_proximity": deadline_stats,
    }