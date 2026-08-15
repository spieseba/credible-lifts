from credible_lifts.ingest.parse_athletes import parse_birthdate_gender


def test_parse_birthdate_gender():
    assert parse_birthdate_gender("Date of birth: 1991-05-17  'M'") == ("1991-05-17", "M")
    assert parse_birthdate_gender("Date of birth: 1991-00-00  'K'") == ("1991-00-00", "W")
    assert parse_birthdate_gender(None) == (None, None)
    assert parse_birthdate_gender("garbage") == (None, None)