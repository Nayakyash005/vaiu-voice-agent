import pytest

from phone_parser import (
    has_phone_number_correction,
    is_valid_phone_number,
    parse_confirmation,
    parsePhoneNumber,
)


@pytest.mark.parametrize(
    ("transcript", "expected"),
    [
        ("nine eight seven six five four three two one zero", "9876543210"),
        ("my number is 9 8 7 6 5 4 3 2 1 0", "9876543210"),
        ("nau aath saat chhe paanch chaar teen do ek shunya", "9876543210"),
        ("nau eight saat 6 paanch 4 teen 2 ek zero", "9876543210"),
        ("98 76 54 32 10", "9876543210"),
        ("987 654 321 0", "9876543210"),
        ("double seven triple nine", "77999"),
        ("oh o zero shunya sifar", "00000"),
        ("नौ आठ सात छह पांच चार तीन दो एक शून्य", "9876543210"),
        ("आठ सात छः पाँच ओह नौ आठ सात छः पाँच चार", "87650987654"),
        ("आठ सात तीन दो एक चार पाँच तीन दो एक", "8732145321"),
        ("nine चार seven पाँच six", "94756"),
        ("mera matlab nine eight seven", "987"),
        ("चार दो तीन फाइव वन टू", "423512"),
        ("nine aath saat 6 5 chaar 3 2 1 zero", "9876543210"),
        ("चार 5 six 7 आठ 9", "456789"),
        ("सुनिए नौ आठ सात छः पाँच चार तीन दो एक", "987654321"),
        ("मेरा मोबाइल नंबर है 4203567861", "4203567861"),
        ("चार पाँच थ्री", "453"),
        ("आठ सात पाँच चार तीन आठ नौ", "8754389"),
    ],
)
def test_parse_phone_number(transcript: str, expected: str) -> None:
    assert parsePhoneNumber(transcript) == expected


@pytest.mark.parametrize(
    "transcript",
    [
        "",
        "please call me tomorrow",
        "one million two",
        "double eleven",
        "चार मोबाइल पाँच",
    ],
)
def test_parse_phone_number_rejects_invalid_input(transcript: str) -> None:
    assert parsePhoneNumber(transcript) is None


def test_parse_phone_number_uses_corrected_sequence() -> None:
    transcript = "nine eight seven six wait sorry correct that 987 654 321 0"

    assert has_phone_number_correction(transcript)
    assert parsePhoneNumber(transcript) == "9876543210"


def test_correction_without_replacement_has_no_digits() -> None:
    assert has_phone_number_correction("wait, sorry")
    assert parsePhoneNumber("nine eight wait, correct that") is None


@pytest.mark.parametrize(
    "transcript",
    [
        "phir se",
        "ek minute",
        "rukho",
        "dobara",
        "galat",
        "galat hai",
        "nahi woh",
        "गलत",
        "नहीं वो",
    ],
)
def test_hinglish_correction_phrases(transcript: str) -> None:
    assert has_phone_number_correction(transcript)
    assert parsePhoneNumber(transcript) is None


def test_correction_phrases_require_context_for_sorry_and_actually() -> None:
    assert not has_phone_number_correction("sorry")
    assert not has_phone_number_correction("actually")
    assert has_phone_number_correction("sorry, my number is 987")
    assert has_phone_number_correction("actually, the number is 987")


@pytest.mark.parametrize(
    ("transcript", "expected"),
    [
        ("yes", "yes"),
        ("yeah", "yes"),
        ("that's right", "yes"),
        ("haan", "yes"),
        ("हाँ", "yes"),
        ("ji haan", "yes"),
        ("sahi", "yes"),
        ("no", "no"),
        ("nahi", "no"),
        ("गलत", "no"),
        ("जी हाँ", "yes"),
    ],
)
def test_confirmation_phrases_are_unicode_safe(transcript: str, expected: str) -> None:
    assert parse_confirmation(transcript) == expected


def test_parse_phone_number_after_long_correction_phrase() -> None:
    assert parsePhoneNumber("nine eight let me correct that, 987 654 321 0") == (
        "9876543210"
    )


@pytest.mark.parametrize(
    ("digits", "expected"),
    [
        ("9876543210", True),
        ("6123456789", True),
        ("5876543210", False),
        ("987654321", False),
        ("98765432100", False),
        ("987654321x", False),
    ],
)
def test_validate_phone_number(digits: str, expected: bool) -> None:
    assert is_valid_phone_number(digits) is expected
