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


def test_asil_aylik_destek_alan_emekli():
    # Eline 20.000 TL (en düşük aylık) geçiyor, asıl aylığı 15.000 TL
    s = emekli.emekli_zammi(20000, "2026-07", asil_aylik=15000)
    assert s["zamli_aylik"] == 17664.00  # zam asıl aylığa uygulanır
    assert s["odenecek_tutar"] == 23552.00
    assert s["gercek_artis"] == 3552.00
    assert "tamamlanır" in s["not"]


def test_asil_aylik_yeni_en_dusugu_asiyor():
    s = emekli.emekli_zammi(20000, "2026-07", asil_aylik=19500)
    assert s["zamli_aylik"] == 22963.20
    assert s["odenecek_tutar"] == 23552.00


def test_en_dusuk_aylik_alana_uyari():
    s = emekli.emekli_zammi(20000, "2026-07")
    assert "asil_aylik" in s["not"]


def test_normal_emekliye_uyari_yok():
    assert "not" not in emekli.emekli_zammi(21000, "2026-07")


def test_asil_aylik_hatali():
    with pytest.raises(ValueError):
        emekli.emekli_zammi(20000, "2026-07", asil_aylik=25000)
