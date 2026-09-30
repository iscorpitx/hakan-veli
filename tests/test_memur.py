import pytest

from zam_hesap import memur


def test_temmuz_2026_memur():
    s = memur.memur_zammi(60000, "memur", "2026-07")
    assert s["zam_orani_yuzde"] == 13.52
    assert s["zamli_net"] == 68112.00
    assert s["en_dusuk_memur_maasi"] == 70224.00


def test_ocak_2026_memur_taban_aylik_notu():
    s = memur.memur_zammi(50000, "memur", "2026-01")
    assert s["zam_orani_yuzde"] == 18.60
    assert "1000 TL" in s["not"]


def test_ocak_2026_memur_emeklisi_en_dusuk_tamamlama():
    s = memur.memur_zammi(20000, "emekli", "2026-01")
    assert s["zamli_net"] == 27772.00
    assert "tamamlanır" in s["not"]


def test_ocak_2026_memur_emeklisi_normal():
    s = memur.memur_zammi(30000, "emekli", "2026-01")
    assert s["zamli_net"] == 35580.00


def test_senaryo_ve_hatalar():
    assert memur.memur_zammi(50000, "memur", "2027-01", 10)["zamli_net"] == 55000.00
    with pytest.raises(ValueError):
        memur.memur_zammi(50000, "memur", "2027-01")
    with pytest.raises(ValueError):
        memur.memur_zammi(50000, "bilinmeyen", "2026-07")
