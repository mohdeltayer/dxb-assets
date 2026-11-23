"""publercheck on the 23 Nov captions (inKONBINI posted twice; the day's GTA VI stories were all different news)."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import publercheck as P

V1 = ('لعبة inKONBINI تفوز بجائزة DevGAMM Choice\n\nحسب بيان رسمي، فازت لعبة inKONBINI: One Store. Many Stories بجائزة '
      'DevGAMM Choice في حفل DevGAMM Awards 2026 الذي أقيم في لشبونة يوم 18 نوفمبر.')
V2 = ('تقرير: فازت لعبة inKONBINI: One Store. Many Stories بجائزة DevGAMM Choice في حفل DevGAMM Awards في لشبونة يوم 18 '
      'نوفمبر، مع عرض خاص على النسخة المطبوعة المحدودة. المصدر: Games Press.')
NEURA = ('مشارك في تجارب Neuralink يلعب GTA VI بعقله\n\nذكر موقع آي جي إن (IGN) أن شركة Neuralink نشرت مقطعا لمشارك في '
         'تجاربها السريرية يلعب GTA VI بعقله فقط عبر شريحة مزروعة في دماغه.')
MEMO = ('ذكر موقع آي جي إن (IGN) أن مطورا في روكستار (Rockstar Games) كرّم والدته الراحلة بنصب تذكاري داخل لعبة GTA VI يمكن '
        'للاعبين زيارته شمال بلدة Hamlet.')


def post(text, state, labels=(), media=()):
    return {'caption': text, 'status': state, 'labels': list(labels), 'media': [{'name': m} for m in media],
            'channel': 'Instagram', 'when': 'Mon, Nov 23 at 12:30 PM UTC+4'}


def test_same_news_published_stops():
    act, line = P.verdict('s2', 'inkonbini-v2', 'inKONBINI: One Store. Many Stories', V2, [post(V1, 'Published')])
    assert act == 'stop' and 'already published' in line


def test_different_gta_news_prepares():
    act, _ = P.verdict('s', 'gta-vi-developer-memorial-mother-ign', 'GTA VI', MEMO, [post(NEURA, 'Published')])
    assert act == 'prepare'


def test_same_story_scheduled_replaces():
    p = post(V1, 'Scheduled', labels=['story:inkonbini-devgamm-choice-award-games-press'])
    act, _ = P.verdict('s', 'inkonbini-devgamm-choice-award-games-press', 'inKONBINI', V2, [p])
    assert act == 'replace'


def test_same_story_by_media_published_stops():
    p = post('x', 'Published', media=['inkonbini-devgamm-choice-award-games-press-reel-v1.mp4'])
    act, _ = P.verdict('s', 'inkonbini-devgamm-choice-award-games-press', 'inKONBINI', V2, [p])
    assert act == 'stop'


def test_same_news_scheduled_under_other_story_stops():
    act, line = P.verdict('s2', 'other-job', 'inKONBINI', V2, [post(V1, 'Scheduled')])
    assert act == 'stop' and 'already scheduled' in line


def test_thresholds():
    assert P.similarity(V1, V2) >= P.SAME_NEWS
    assert P.similarity(NEURA, MEMO) < P.SAME_NEWS
