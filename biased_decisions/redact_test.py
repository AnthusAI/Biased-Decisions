"""Specs for email redaction in published text."""
from biased_decisions.redact import redact_contact


def test_an_email_address_in_the_middle_of_a_sentence_is_replaced():
    text = "She can be reached at jane@example.com for details."
    result = redact_contact(text)
    assert result == "She can be reached at [email removed] for details."
    assert "jane@example.com" not in result


def test_text_without_an_email_address_is_unchanged():
    text = "This is a simple biography with no contact information."
    result = redact_contact(text)
    assert result == text


def test_multiple_email_addresses_are_all_replaced():
    text = "Contact alice@example.com or bob@example.org for more info."
    result = redact_contact(text)
    assert result == "Contact [email removed] or [email removed] for more info."
    assert "@" not in result


def test_email_with_complex_local_and_domain_parts():
    text = "Email user.name+tag@sub.domain.co.uk for assistance."
    result = redact_contact(text)
    assert result == "Email [email removed] for assistance."
