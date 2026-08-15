from bs4 import BeautifulSoup

from credible_lifts.ingest.parse_competitions import athlete_id, attempt, cell, num

ROW_HTML = """
<tr>
<td class="col-place">1</td>
<td class="col-name"><a href="/public/zawodnik/1000000000-erwin-fake"> Erwin Fake </a></td>
<td><a href="/public/federacja/99-fak">FAK</a></td>
<td class="col-weight">200.00</td>
<td class="col-rw">200</td>
<td class="col-rw">210</td>
<td class="col-rw neg">220</td>
</tr>
"""


def test_cell():
    tds = BeautifulSoup(ROW_HTML, "html.parser").find_all("td")
    headers = ["rank", "name", "nation", "bodyweight", "attempt-1", "attempt-2", "attempt-3"]
    idx = {name:i for i,name in enumerate(headers)}
    assert int(cell("rank", tds, idx).get_text(" ", strip=True)) == 1
    assert cell("name", tds, idx).get_text(" ", strip=True) == "Erwin Fake"
    assert cell("club", tds, idx) is None

def test_num():
    assert num("1") == 1
    assert num("3.141592") == 3.141592
    assert num("—") is None
    assert num("what") == "?what"

def test_athlete_id():
    tr = BeautifulSoup(ROW_HTML, "html.parser").select_one("tr")
    tr_no_athlete = BeautifulSoup('<tr><td><a href="/public/federacja/99-fak">FAK</a></td></tr>', "html.parser").tr
    assert athlete_id(tr) == 1000000000
    assert athlete_id(tr_no_athlete) is None

def test_attempt():
    tds = BeautifulSoup(ROW_HTML, "html.parser").find_all("td")
    headers = ["rank", "name", "nation", "bodyweight", "attempt-1", "attempt-2", "attempt-3"]
    idx = {name:i for i,name in enumerate(headers)}
    assert attempt(cell("attempt-1", tds, idx)) == 200
    assert attempt(cell("attempt-2", tds, idx)) == 210
    assert attempt(cell("attempt-3", tds, idx)) == -220
