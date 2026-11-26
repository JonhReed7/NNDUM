import re
from pathlib import Path
from app.schemas.metrics_schemas import ReadmeCompleteness

# Паттерны заголовков для обязательных разделов (поддержка RU и EN)
INSTALL_RUN_HEADERS = re.compile(
    r"(установк|запуск|старт|сборк|развертывани|использовани|install|setup|getting started|quick start|usage|run|deploy)",
    re.IGNORECASE,
)

STRUCTURE_HEADERS = re.compile(
    r"(структур|архитектур|директори|папк|модул|состав проекта|structure|architecture|layout|directories|folder)",
    re.IGNORECASE,
)

ABOUT_HEADERS = re.compile(
    r"(о проект|описани|введени|цель|задач|about|overview|description|introduction)",
    re.IGNORECASE,
)

# Характерные команды запуска/установки в блоках кода
CLI_COMMANDS_PATTERN = re.compile(
    r"(pip install|poetry install|npm install|yarn |pnpm |docker(-compose| compose| build| run)|uvicorn|python\s+|go run|make\s+)",
    re.IGNORECASE,
)


def _extract_sections(markdown_text: str) -> tuple[str, list[tuple[str, str]]]:
    """
    Разбивает Markdown-текст на вводную часть (до первого ##)
    и список кортежей (заголовок_секции, текст_секции).
    """
    lines = markdown_text.splitlines()
    intro_lines: list[str] = []
    sections: list[tuple[str, str]] = []

    current_header: str | None = None
    current_body: list[str] = []

    for line in lines:
        # Ищем заголовки уровня ## и глубже (главный заголовок # обычно название проекта)
        header_match = re.match(r"^#{2,6}\s+(.+)", line.strip())
        if header_match:
            if current_header is not None:
                sections.append((current_header, "\n".join(current_body).strip()))
            current_header = header_match.group(1).strip()
            current_body = []
        else:
            if current_header is None:
                # Игнорируем главный заголовок # и бейджи ![...], собираем только текст описания
                if not line.strip().startswith("#") and not line.strip().startswith("[!["):
                    intro_lines.append(line)
            else:
                current_body.append(line)

    if current_header is not None:
        sections.append((current_header, "\n".join(current_body).strip()))

    return "\n".join(intro_lines).strip(), sections


def calculate_readme_completeness(repo_dir: str | Path) -> ReadmeCompleteness:
    """
    Метрика №5: Полнота README.
    Проверяет наличие файла README в корне репозитория и трёх ключевых разделов:
    1. Описание проекта
    2. Инструкции по установке и запуску
    3. Краткий обзор структуры проекта
    """
    root = Path(repo_dir)
    readme_file: Path | None = None

    # Ищем README без учета регистра (README.md, readme.md, README.rst, README)
    for candidate in root.iterdir():
        if candidate.is_file() and candidate.stem.lower() == "readme":
            readme_file = candidate
            break

    if not readme_file:
        return ReadmeCompleteness.model_validate({
            "has_readme": False,
            "file_name": None,
            "completeness_percent": 0.0,
            "checks": {
                "has_description": False,
                "has_install_and_run": False,
                "has_structure_overview": False,
            },
            "missing_sections": [
                "Файл README.md отсутствует в корне репозитория"
            ],
        })

    content = readme_file.read_text(encoding="utf-8", errors="ignore").strip()
    intro_text, sections = _extract_sections(content)

    # 1. Проверка описания проекта: либо содержательный текст в шапке, либо отдельный раздел
    has_description = len(intro_text) >= 50 or any(
        ABOUT_HEADERS.search(header) and len(body) >= 30
        for header, body in sections
    )

    # 2. Проверка инструкций по установке и запуску: профильный заголовок или блок кода с командами
    has_install_header = any(
        INSTALL_RUN_HEADERS.search(header) and len(body) >= 20
        for header, body in sections
    )
    has_code_blocks_with_cmds = "```" in content and bool(CLI_COMMANDS_PATTERN.search(content))
    has_install_and_run = has_install_header or has_code_blocks_with_cmds

    # 3. Проверка обзора структуры: профильный заголовок или дерево каталогов (├── / └──)
    has_structure_header = any(
        STRUCTURE_HEADERS.search(header) and len(body) >= 20
        for header, body in sections
    )
    has_directory_tree = "├──" in content or "└──" in content
    has_structure_overview = has_structure_header or has_directory_tree

    checks = {
        "has_description": has_description,
        "has_install_and_run": has_install_and_run,
        "has_structure_overview": has_structure_overview,
    }

    passed_count = sum(1 for passed in checks.values() if passed)
    completeness_percent = round((passed_count / len(checks)) * 100, 2)

    missing_sections = []
    if not has_description:
        missing_sections.append("Описание проекта")
    if not has_install_and_run:
        missing_sections.append("Инструкции по установке и запуску")
    if not has_structure_overview:
        missing_sections.append("Краткий обзор структуры проекта")

    return ReadmeCompleteness.model_validate({
        "has_readme": True,
        "file_name": readme_file.name,
        "completeness_percent": completeness_percent,
        "checks": checks,
        "missing_sections": missing_sections,
    })
