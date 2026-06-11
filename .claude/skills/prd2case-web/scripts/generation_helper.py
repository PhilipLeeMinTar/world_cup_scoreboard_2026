
import argparse
from pathlib import Path


def _resolve_existing_file(path_str, label):
    path = Path(path_str)
    if not path.is_absolute():
        path = Path.cwd() / path
    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")
    return path


def _resolve_session_dir(session):
    workspace_root = Path.cwd().resolve()
    sessions_root = workspace_root / "sessions"
    sessions_root.mkdir(parents=True, exist_ok=True)

    session_path = Path(session)
    if session_path.is_absolute():
        normalized_parts = [part for part in session_path.parts if part and part != "/"]
        if "sessions" in normalized_parts:
            return session_path.resolve()
        return sessions_root / session_path.name

    if session_path.parts and session_path.parts[0] == "sessions":
        return (workspace_root / session_path).resolve()
    return (sessions_root / session_path).resolve()


def _ensure_prompt_template_dir(session):
    prompt_template_dir = _resolve_session_dir(session) / "prompt_template"
    prompt_template_dir.mkdir(parents=True, exist_ok=True)
    return prompt_template_dir


def _load_template(template_name):
    script_dir = Path(__file__).resolve().parent
    skill_root = script_dir.parent
    template_path = skill_root / "assets" / "generation_templates" / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"instruction template not found: {template_path}")
    return template_path.read_text(encoding="utf-8")


def prepare_test_analysis_instruction(input_document_path, session):
    """
    Build the test analysis instruction file for the given session.

    Steps:
    1. Read content from input_document_path.
    2. Ensure session/prompt_template exists.
    3. Load assets/generation_templates/test_analysis_instruction.template.md.
    4. Replace input placeholder with input document content.
    5. Write session/prompt_template/test_analysis_instruction.md.

    Returns:
        str: Absolute path of the generated instruction file.
    """
    source_doc = _resolve_existing_file(input_document_path, "input document")
    input_document_content = source_doc.read_text(encoding="utf-8")

    prompt_template_dir = _ensure_prompt_template_dir(session)
    template_content = _load_template("test_analysis_instruction.template.md")
    instruction_content = (
        template_content.replace("{{input_document}}", input_document_content)
        .replace("{{input_template}}", input_document_content)
    )

    output_path = prompt_template_dir / "test_analysis_instruction.md"
    output_path.write_text(instruction_content, encoding="utf-8")
    return str(output_path)


def prepare_framework_generation_instruction(
    input_document_path,
    test_analysis_path,
    experiment_setting_path,
    session,
):
    """
    Build the framework generation instruction file for the given session.

    Steps:
    1. Read the original input document, the generated test analysis document, and experiment settings.
    2. Ensure session/prompt_template exists.
    3. Load assets/generation_templates/framework_generation_instruction.template.md.
    4. Replace placeholders with the original document, experiment settings, and raw test analysis content.
    5. Write session/prompt_template/framework_generation_instruction.md.

    Returns:
        str: Absolute path of the generated instruction file.
    """
    input_document = _resolve_existing_file(input_document_path, "input document")
    test_analysis = _resolve_existing_file(test_analysis_path, "test analysis document")
    experiment_setting = _resolve_existing_file(
        experiment_setting_path, "experiment setting document"
    )

    input_document_content = input_document.read_text(encoding="utf-8")
    test_analysis_content = test_analysis.read_text(encoding="utf-8")
    experiment_content = experiment_setting.read_text(encoding="utf-8")

    prompt_template_dir = _ensure_prompt_template_dir(session)
    template_content = _load_template("framework_generation_instruction.template.md")
    instruction_content = (
        template_content.replace("{{input_document}}", input_document_content)
        .replace("{{experiment}}", experiment_content)
        .replace("{{test_analysis}}", test_analysis_content)
    )

    output_path = prompt_template_dir / "framework_generation_instruction.md"
    output_path.write_text(instruction_content, encoding="utf-8")
    return str(output_path)


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Prepare PRD2Case prompt templates for agent-driven generation."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    test_analysis_parser = subparsers.add_parser(
        "test-analysis",
        help="Prepare the prompt file for test analysis generation.",
    )
    test_analysis_parser.add_argument("input_document_path", help="Path to the source document.")
    test_analysis_parser.add_argument("session", help="Session dir name or path.")

    framework_parser = subparsers.add_parser(
        "framework-generation",
        help="Prepare the prompt file for framework generation.",
    )
    framework_parser.add_argument("input_document_path", help="Path to the source document.")
    framework_parser.add_argument(
        "test_analysis_path",
        help="Path to the generated test analysis document.",
    )
    framework_parser.add_argument(
        "experiment_setting_path",
        help="Path to the experiment setting document.",
    )
    framework_parser.add_argument("session", help="Session dir name or path.")

    return parser.parse_args()


def main():
    args = _parse_args()

    if args.command == "test-analysis":
        output_path = prepare_test_analysis_instruction(args.input_document_path, args.session)
    else:
        output_path = prepare_framework_generation_instruction(
            args.input_document_path,
            args.test_analysis_path,
            args.experiment_setting_path,
            args.session,
        )

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

