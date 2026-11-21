"""Credit ladder (Mohammad, 21 Nov 2026): steps in order, never dropped, Arabic first word on every row."""
import creditfit as C

M = lambda r, s: len(r) * s * 0.5          # a stand-in width: half the size per character


def test_full_form_fits_one_line():
    g = C.fit('المصدر: نينتيندو (Nintendo)', 36, M, 814)
    assert g['step'] == 1 and g['rows'] == ['المصدر: نينتيندو (Nintendo)']


def test_latin_only_before_short_names():
    t = 'المصدر: نوتبوك تشيك (Notebookcheck)،\nولقطات من روكستار (Rockstar Games)'
    room = M('المصدر: Notebookcheck · اللقطات: Rockstar Games', 36)
    g = C.fit(t, 36, M, room)
    assert g['step'] == 2 and g['rows'] == ['المصدر: Notebookcheck · اللقطات: Rockstar Games']


def test_short_names_then_primary_only():
    t = 'المصدر: ميتاكريتيك ونوتبوك تشيك (Notebookcheck)، ولقطات من روكستار (Rockstar Games)'
    g = C.fit(t, 36, M, M('المصدر: Metacritic, Notebookcheck · اللقطات: Rockstar', 36))
    assert g['step'] == 3
    g = C.fit(t, 36, M, M('المصدر: Metacritic · اللقطات: Rockstar', 36))
    assert g['step'] == 4 and g['rows'] == ['المصدر: Metacritic · اللقطات: Rockstar']


def test_smaller_type_then_two_lines():
    t = 'المصدر: ميتاكريتيك ونوتبوك تشيك (Notebookcheck)، ولقطات من روكستار (Rockstar Games)'
    short = 'المصدر: Metacritic · اللقطات: Rockstar'
    g = C.fit(t, 36, M, M(short, 32))
    assert g['step'] == 5 and g['size'] == 32
    g = C.fit(t, 36, M, M('المصدر: Metacritic', 36))
    assert g['step'] == 6 and g['rows'] == ['المصدر: Metacritic', 'اللقطات: Rockstar']
    assert all(C._arabic_first(r) for r in g['rows'])


def test_nothing_fits_is_none_never_dropped():
    assert C.fit('المصدر: نوتبوك تشيك (Notebookcheck)', 36, M, 50) is None


def test_other_credits_keep_their_words():
    assert C.forms('الصورة: Wikimedia Commons') == [(1, 'الصورة: Wikimedia Commons')]
    assert C.forms('لقطات من Fortnite')[1] == (2, 'اللقطات: Fortnite')
