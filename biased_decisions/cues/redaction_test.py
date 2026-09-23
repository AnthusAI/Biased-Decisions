"""Feature: first-name redaction.

Ported from Jev-Flywheel's ``jev_flywheel/counterfactual_test.py`` (the ``redact_names`` half).
Skipped when spaCy's ``en_core_web_sm`` model is not installed (it is an optional ``build``
extra, not a core dependency of this package).
"""
import pytest

from biased_decisions.cues.redaction import redact_names, redact_names_batch

try:
    import spacy
    spacy.load("en_core_web_sm")
    _HAS_NAME_MODEL = True
except (ImportError, OSError):
    _HAS_NAME_MODEL = False

requires_name_model = pytest.mark.skipif(
    not _HAS_NAME_MODEL,
    reason="spacy en_core_web_sm is not installed (pip install '.[build]')")


@requires_name_model
def test_first_name_in_a_person_span_is_redacted():
    redaction = redact_names("Jennifer has extensive research experience.")
    assert redaction.text == "[name] has extensive research experience."
    assert redaction.redacted == 1


@requires_name_model
def test_possessive_name_keeps_the_apostrophe_s():
    redaction = redact_names("Jennifer's research won an award.")
    assert redaction.text == "[name]'s research won an award."
    assert redaction.redacted == 1


@requires_name_model
def test_surname_alone_is_not_on_the_name_list_so_is_untouched():
    # "Smith" is a surname, not a first name, and is never on pools/first_names.txt.
    redaction = redact_names("Dr. Smith is a surgeon.")
    assert redaction.text == "Dr. Smith is a surgeon."
    assert redaction.redacted == 0


@requires_name_model
def test_a_first_name_outside_any_person_span_is_left_alone():
    # "May" is on the first-name list but reads as the month here, not a PERSON entity.
    redaction = redact_names("She graduated in May with honors.")
    assert redaction.redacted == 0


@requires_name_model
def test_batch_matches_the_single_text_path():
    texts = ["Jennifer has extensive research experience.", "Dr. Smith is a surgeon."]
    batched = redact_names_batch(texts)
    singles = [redact_names(t) for t in texts]
    assert [r.text for r in batched] == [r.text for r in singles]
    assert [r.redacted for r in batched] == [r.redacted for r in singles]
