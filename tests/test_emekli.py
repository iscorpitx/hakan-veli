import pytest

from zam_hesap import emekli


@pytest.mark.parametrize(
    "aylik,beklenen",
    # Temmuz 2026 %17,76 zam sonrası basında yayımlanan örnekler (TL, küsurat atılmış)
    [(21000, 24729), (22000, 25907), (23000, 27084), (24000, 28262)],
)
def test_temmuz_2026_ornekleri(aylik, beklenen):
    s = emekli.emekli_zammi(aylik, "2026-07")
    assert int(s["zamli_aylik"]) == beklenen
    assert s["odenecek_tutar"] == s["zamli_aylik"]


def test_en_dusuk_aylik_tamamlamasi():
    s = emekli.emekli_zammi(16000, "2026-07")
    assert s["zamli_aylik"] == 18841.60
    assert s["odenecek_tutar"] == 23552.00
    assert "not" in s


def test_ocak_2026():
    s = emekli.emekli_zammi(10000, "2026-01")
    assert s["zam_orani_yuzde"] == 12.19
    assert s["odenecek_tutar"] == 20000.00


def test_varsayilan_en_son_donem():
    assert emekli.emekli_zammi(30000)["donem"] == "2026-07"


def test_senaryo_gelecek_donem():
    s = emekli.emekli_zammi(20000, "2027-01", 14.5)
    assert s["zamli_aylik"] == 22900.00
    assert s["kaynak"] == "kullanıcı senaryosu"
    assert "odenecek_tutar" not in s


def test_kayitsiz_donem_oransiz_hata():
    with pytest.raises(ValueError):
        emekli.emekli_zammi(20000, "2027-01")


def test_kumulatif_enflasyon_ocak_haziran_2026():
    s = emekli.kumulatif_enflasyon([4.84, 2.96, 1.94, 4.18, 1.71, 0.99])
    # TÜİK resmi oranı %17,76 (endeksten); aylık yuvarlanmış oranlardan ~0,01 puan fark beklenir.
    assert s["kumulatif_yuzde"] == pytest.approx(17.76, abs=0.02)
