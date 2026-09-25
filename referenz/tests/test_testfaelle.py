"""Echte Testfälle aus docs/testfaelle/ (ENT-030)."""
import datetime, os
from mtref.bars import load_tradingview_csv
from mtref.gwl import causal_depth, htf_swings, session_groups

D = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "testfaelle")


def groups_min(bars, m):
    g, last = [], None
    for x in bars:
        d = datetime.datetime.strptime(x.time, "%Y-%m-%d %H:%M")
        k = (d.date(), (d.hour * 60 + d.minute) // m)
        if k != last:
            g.append([]); last = k
        g[-1].append(x)
    return g


def test_01_cl_2h_gwl_aus_tageskerzen():                                 # ENT-084, ENT-086
    b = load_tradingview_csv(os.path.join(D, "test01_cl1_120.csv"))
    f = causal_depth(htf_swings(b, session_groups(b), 0.01), 0.382)
    assert [x.price for x in f if b[x.idx].time >= "2026-08-05"] == [74.24, 84.61, 80.09, 87.69, 79.62, 106.75]


def test_02_mnq_1m_gwl_aus_10min():                                      # ENT-085, ENT-087
    b = load_tradingview_csv(os.path.join(D, "test02_mnq_1m.csv"))
    p = [x.price for x in causal_depth(htf_swings(b, groups_min(b, 10), 0.25), 0.382)
         if "2026-09-25 00:30" <= b[x.idx].time <= "2026-09-25 11:40"]
    assert p == [30682.0, 30814.5, 30760.75, 30795.0, 30764.5, 30814.25, 30766.5, 30792.25, 30767.25,
                 30813.75, 30789.0, 30905.25, 30863.75, 30903.0, 30870.25, 30905.0, 30837.5, 30963.0,
                 30900.0, 30942.5, 30911.25, 30998.5]
