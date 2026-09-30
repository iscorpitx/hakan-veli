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


def test_memur_zam_formulu_temmuz_2026_resmi():
    # Önceki dönem toplu sözleşme %11, Ocak-Haziran 2026 enflasyonu %17,76, yeni dönem %7
    s = memur.memur_zam_senaryosu(
        60000, toplu_sozlesme_yuzde=7, onceki_toplu_sozlesme_yuzde=11, alti_aylik_enflasyon_yuzde=[17.76]
    )
    sen = s["senaryolar"][0]
    assert sen["enflasyon_farki_yuzde"] == 6.09
    assert sen["toplam_zam_yuzde"] == 13.52  # resmi Temmuz 2026 oranı


def test_memur_enflasyon_toplu_sozlesmenin_altinda():
    s = memur.memur_zam_senaryosu(
        50000, "emekli", toplu_sozlesme_yuzde=5, onceki_toplu_sozlesme_yuzde=7, alti_aylik_enflasyon_yuzde=[4]
    )
    sen = s["senaryolar"][0]
    assert sen["enflasyon_farki_yuzde"] == 0
    assert sen["zamli_net"] == 52500.00


def test_memur_zam_senaryosu_dogrudan_oranlar():
    s = memur.memur_zam_senaryosu(60000, zam_oranlari_yuzde=[10, 20])
    assert [x["zamli_net"] for x in s["senaryolar"]] == [66000.00, 72000.00]


def test_memur_zam_senaryosu_eksik_girdi():
    with pytest.raises(ValueError):
        memur.memur_zam_senaryosu(60000)
    with pytest.raises(ValueError):
        memur.memur_zam_senaryosu(60000, alti_aylik_enflasyon_yuzde=[10])
