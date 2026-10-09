"""Deterministic parsing and validation for spoken mobile numbers."""

import re
import unicodedata

_DIGIT_WORDS = {
    "zero": "0",
    "oh": "0",
    "o": "0",
    "जीरो": "0",
    "ओ": "0",
    "ओह": "0",
    "shunya": "0",
    "sifar": "0",
    "one": "1",
    "वन": "1",
    "ek": "1",
    "two": "2",
    "टू": "2",
    "do": "2",
    "three": "3",
    "थ्री": "3",
    "teen": "3",
    "four": "4",
    "फोर": "4",
    "chaar": "4",
    "five": "5",
    "फाइव": "5",
    "paanch": "5",
    "six": "6",
    "सिक्स": "6",
    "chhe": "6",
    "seven": "7",
    "सेवन": "7",
    "saat": "7",
    "eight": "8",
    "एट": "8",
    "aath": "8",
    "nine": "9",
    "नाइन": "9",
    "nau": "9",
    "शून्य": "0",
    "सिफर": "0",
    "एक": "1",
    "दो": "2",
    "तीन": "3",
    "चार": "4",
    "पाँच": "5",
    "पांच": "5",
    "छह": "6",
    "छः": "6",
    "सात": "7",
    "आठ": "8",
    "नौ": "9",
}
_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
_FILLER_WORDS = {
    "and",
    "me",
    "please",
    "सुनिए",
}
_PHONE_CONTEXT_WORDS = {
    "is",
    "it",
    "its",
    "mobile",
    "my",
    "number",
    "phone",
    "the",
    "मेरा",
    "मोबाइल",
    "नंबर",
    "है",
}
_CORRECTION_PHRASES = (
    ("let", "me", "correct", "that"),
    ("let", "me", "correct"),
    ("correct", "that"),
    ("correct",),
    ("scratch", "that"),
    ("start", "over"),
    ("i", "mean"),
    ("sorry", "my", "number", "is"),
    ("sorry", "the", "number", "is"),
    ("actually", "my", "number", "is"),
    ("actually", "the", "number", "is"),
    ("sorry", "thats", "wrong"),
    ("actually", "thats", "wrong"),
    ("galat", "hai"),
    ("ek", "minute"),
    ("phir", "se"),
    ("mera", "matlab"),
    ("nahi", "woh"),
    ("nahin", "woh"),
    ("गलत", "है"),
    ("एक", "मिनट"),
    ("फिर", "से"),
    ("मेरा", "मतलब"),
    ("नहीं", "वो"),
    ("नहीं", "वह"),
    ("rukho",),
    ("ruko",),
    ("dobara",),
    ("galat",),
    ("फिरसे",),
    ("दोबारा",),
    ("रुको",),
    ("गलत",),
    ("wait",),
    ("correction",),
)
_YES_CONFIRMATIONS = {
    "yes",
    "yeah",
    "yep",
    "correct",
    "confirm",
    "thats right",
    "that is right",
    "haan",
    "han",
    "ji haan",
    "sahi",
    "bilkul",
    "हाँ",
    "हां",
    "जी हाँ",
    "जी हां",
    "सही",
}
_NO_CONFIRMATIONS = {
    "no",
    "nope",
    "incorrect",
    "wrong",
    "thats wrong",
    "that is wrong",
    "nahi",
    "nahin",
    "nahi hai",
    "galat",
    "नहीं",
    "नहि",
    "गलत",
}
_TOKEN_PATTERN = re.compile(r"[a-z]+|[\u0900-\u097f]+|\d+", re.IGNORECASE)


def _tokens(transcript: str) -> list[str]:
    normalized = transcript.lower().translate(_DEVANAGARI_DIGITS)
    return _TOKEN_PATTERN.findall(normalized.replace("'", ""))


def _correction_suffix_start(tokens: list[str]) -> int | None:
    suffix_start = None
    index = 0
    while index < len(tokens):
        for phrase in _CORRECTION_PHRASES:
            if tuple(tokens[index : index + len(phrase)]) == phrase:
                suffix_start = index + len(phrase)
                index += len(phrase) - 1
                break
        index += 1
    return suffix_start


def has_phone_number_correction(transcript: str) -> bool:
    """Return whether the transcript contains an explicit restart/correction cue."""
    return _correction_suffix_start(_tokens(transcript)) is not None


def normalize_confirmation(transcript: str) -> str:
    """Normalize confirmation text while preserving Unicode letters and marks."""
    normalized = unicodedata.normalize("NFKC", transcript).casefold()
    characters = []
    for character in normalized:
        if character in {"'", "\u2019"}:
            continue
        category = unicodedata.category(character)
        if character.isspace() or category[0] in {"L", "M"}:
            characters.append(character)
        else:
            characters.append(" ")
    return " ".join("".join(characters).split())


def parse_confirmation(transcript: str) -> str | None:
    """Return ``yes`` or ``no`` for a supported exact confirmation phrase."""
    answer = normalize_confirmation(transcript)
    if answer in _YES_CONFIRMATIONS:
        return "yes"
    if answer in _NO_CONFIRMATIONS:
        return "no"
    return None


def parsePhoneNumber(transcript: str) -> str | None:  # noqa: N802
    """Convert spoken English, Hindi, or numeric digit groups into digits.

    ``double`` and ``triple`` repeat the following digit. If a correction cue
    occurs, only the sequence after the last cue is parsed. Unknown words are
    rejected rather than silently discarded.
    """
    tokens = _tokens(transcript)
    correction_start = _correction_suffix_start(tokens)
    if correction_start is not None:
        tokens = tokens[correction_start:]

    if not tokens:
        return None

    digit_positions = [
        index
        for index, token in enumerate(tokens)
        if token.isdigit() or token in _DIGIT_WORDS
    ]
    first_digit = min(digit_positions, default=len(tokens))
    last_digit = max(digit_positions, default=-1)

    digits: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in {"double", "triple"}:
            if index + 1 >= len(tokens):
                return None
            next_token = tokens[index + 1]
            digit = _DIGIT_WORDS.get(next_token)
            if digit is None and next_token.isdigit() and len(next_token) == 1:
                digit = next_token
            if digit is None:
                return None
            digits.extend(digit * (2 if token == "double" else 3))
            index += 2
            continue

        if token.isdigit():
            digits.extend(token)
        elif token in _DIGIT_WORDS:
            digits.append(_DIGIT_WORDS[token])
        elif token not in _FILLER_WORDS:
            is_surrounding_phone_context = token in _PHONE_CONTEXT_WORDS and (
                index < first_digit or index > last_digit
            )
            if not is_surrounding_phone_context:
                return None
        index += 1

    return "".join(digits) or None


def is_valid_phone_number(digits: str) -> bool:
    """Return whether digits are a valid 10-digit Indian mobile number."""
    return (
        len(digits) == 10
        and digits.isascii()
        and digits.isdigit()
        and digits[0] in "6789"
    )
