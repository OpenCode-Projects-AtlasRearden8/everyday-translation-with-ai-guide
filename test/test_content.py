"""Content tests: the manual says what the project promises it says.

Guardrails for the original goal:
- covers school/medical/rental/utility/government paper and human-office
  alternatives;
- hard lines about signed legal or medical decisions are present;
- privacy guidance about personal details and cloud tools is present;
- verification checklist and glossary exist;
- it is explicitly NOT a language-learning guide;
- no secrets, keys, or personal data anywhere; no external network calls.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

CHAPTERS = [
    "00-introduction.md",
    "01-read-the-structure-first.md",
    "02-everyday-documents.md",
    "03-medical-paperwork.md",
    "04-rental-and-housing.md",
    "05-government-forms.md",
    "06-privacy-first.md",
    "07-verifying-a-translation.md",
    "08-ask-a-human-instead.md",
    "09-hard-lines.md",
    "10-verification-checklist.md",
    "11-glossary.md",
]


def doc(name):
    return (DOCS / name).read_text(encoding="utf-8").lower()


def test_all_chapters_exist():
    for name in CHAPTERS:
        assert (DOCS / name).exists(), name


def test_every_chapter_has_exactly_one_h1():
    for name in CHAPTERS:
        h1s = re.findall(r"^#\s+", doc(name), re.M)
        assert len(h1s) == 1, f"{name} has {len(h1s)} H1s"


def single(chapter, phrase, msg):
    """`phrase` appears at least once in that chapter."""
    assert phrase in doc(chapter), f"{msg}: missing {phrase!r} in {chapter}"


def test_topics_covered():
    single("02-everyday-documents.md", "school notices", "school")
    single("02-everyday-documents.md", "utility letters", "utility")
    single("03-medical-paperwork.md", "medical paperwork", "medical")
    single("04-rental-and-housing.md", "rental and housing", "rental")
    single("05-government-forms.md", "government forms", "government")
    single("08-ask-a-human-instead.md", "human", "human offices")


def test_structure_before_translation_is_teaching():
    single(
        "01-read-the-structure-first.md",
        "read the document's structure first",
        "structure chapter",
    )
    single("01-read-the-structure-first.md", "do not translate this yet", "structure prompt")


def test_hard_lines_present():
    single(
        "09-hard-lines.md",
        "never for anything you sign",
        "signed-decision hard line",
    )
    single(
        "09-hard-lines.md",
        "never for medical decisions",
        "medical-decision hard line",
    )
    single("00-introduction.md", "signed legal or medical decision", "intro hard line")


def test_human_office_alternatives():
    single("08-ask-a-human-instead.md", "what to ask a human office", "chapter title")
    single(
        "08-ask-a-human-instead.md",
        "i need an interpreter",
        "interpreter phrase",
    )


def test_privacy_chapter():
    single(
        "06-privacy-first.md",
        "keeping personal details out of cloud tools",
        "privacy title",
    )
    single("06-privacy-first.md", "[name]", "placeholder scheme")
    single("06-privacy-first.md", "never paste", "red-list rule")
    single("06-privacy-first.md", "local ai", "local-first option")


def test_verification_checklist_is_present_and_actionable():
    text = doc("10-verification-checklist.md")
    boxes = text.count("- [ ]")
    assert boxes >= 15, f"checklist too thin: {boxes} items"
    single("10-verification-checklist.md", "step 0", "safety step")
    single("10-verification-checklist.md", "back-translation", "round trip")


def test_glossary_has_core_terms():
    text = doc("11-glossary.md")
    for term in ("anchor term", "certified translation", "de-identification",
                 "local ai", "red list", "right to interpreter",
                 "machine translation", "placeholder"):
        assert f"**{term}" in text, f"glossary missing {term}"


def test_distinct_from_language_learning_guide():
    text = doc("00-introduction.md")
    assert "language-learning" in text, "must disclaim language-learning scope"
    assert "vocabulary drills" in text or "conjugation" in text


def test_warm_voice_intro():
    # warm voice markers in intro
    text = doc("00-introduction.md")
    assert "welcome" in text
    assert "condescend" in text


def test_no_personal_data_or_secrets():
    secret_patterns = [
        re.compile(r"sk-[A-Za-z0-9]{10,}"),          # OpenAI-style keys
        re.compile(r"AKIA[0-9A-Z]{16}"),             # AWS keys
        re.compile(r"ghp_[A-Za-z0-9]{20,}"),         # GitHub tokens
        re.compile(r"(?i)password\s*[:=]\s*\S"),
        re.compile(r"(?i)api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9]"),
    ]
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix in {".pyc", ".png", ".jpg"}:
            continue
        if ".git" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, ValueError):
            continue
        for pat in secret_patterns:
            assert not pat.search(text), f"possible secret in {path}"


def test_no_placeholders_leaked_from_examples():
    """Example placeholders like [STUDENT ID] are fine; real 9-digit
    US-style accounts or such are not."""
    nine_digit = re.compile(r"\b[2-9]\d{8}\b")
    for name in CHAPTERS:
        text = doc(name)
        assert not nine_digit.search(text), f"possible personal number in {name}"


def test_no_external_network_calls():
    url = re.compile(r"https?://")
    for name in CHAPTERS:
        assert not url.search(doc(name)), f"external URL in {name}"


def test_cross_references_resolve():
    """Every 'Chapter N' reference points to a chapter that exists here."""
    available = {int(re.match(r"^(\d+)", p.name).group(1)) for p in DOCS.glob("*.md")}
    refs = re.compile(r"[Cc]hapter (\d+)")
    for name in CHAPTERS:
        text = doc(name)
        # Ignore the document's own number header lines.
        own_num = int(re.match(r"^(\d+)", name).group(1))
        for ref in refs.findall(text):
            assert int(ref) in available, \
                f"{name} references missing Chapter {ref}"
