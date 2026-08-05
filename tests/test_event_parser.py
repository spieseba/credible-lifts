from bs4 import BeautifulSoup

from credible_lifts.parse_event import parse_snatchjerk_card

CARD_HTML = """
<div class="card">
 <p>Rank: 1</p> 
 <p>FAKE Erwin</p>
 <p>FAK</p>
 <p>Born: Jan 1, 2000</p>
 <p>B.weight: 200.00</p>
 <p>Group: A</p>
 <p>1: 200</p>
 <p><strike>2: 210</strike></p>
 <p>3: 220</p>
 <p>Total: 220</p>
</div>
"""

def test_parse_snatchjerk_card():
    card = BeautifulSoup(CARD_HTML, "html.parser").select_one("div.card")
    row = parse_snatchjerk_card(card)
    assert row["name"] == "FAKE Erwin"
    assert row["bodyweight"] == 200.0
    assert row["attempt-1"] == 200
    assert row["attempt-2"] is None