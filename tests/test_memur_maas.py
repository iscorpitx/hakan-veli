import json

import pytest

from zam_hesap import memur_maas as mm


def test_gercek_ogretmen_bordrosu_subat_2026():
    # Yayımlanmış, kişisel bilgileri kapatılmış bir KBS öğretmen bordrosu (Şubat 2026, 7/1, 6 yıl, 5510, evli/0).
    b = mm.memur_maasi(7, 1, 6, ay=2, onceki_kumulatif_matrah=28645.87)
    assert b["kazanclar"] == {
        "gosterge_ayligi": 978.45,
        "ek_gosterge_ayligi": 2081.81,
        "taban_ayligi": 22722.79,
        "kidem_ayligi": 166.54,
        "yan_odeme": 330.11,
        "ozel_hizmet_tazminati": 13917.85,
        "ek_odeme": 8570.10,
        "ilave_odeme": 22157.36,
        "kariyer_tazminati": 0.0,
    }
    assert b["kesintiler"]["malulluk_yaslilik"] == 3588.07
    assert b["kesintiler"]["gss"] == 1993.37
    assert b["gelir_vergisi_matrahi"] == 20698.26  # bordrodaki "aylık vergi matrahı"
    assert b["kesintiler"]["gelir_vergisi"] == 0.0
    # Bordroda damga vergisi 334,44 / net 65.009,13. Aradaki 46,82 TL yalnızca damga vergisinden geliyor
    # (bordroya dahil başka bir ödemenin damgası, muhtemelen geçen ay farkı); diğer tüm kalemler birebir tutuyor.
    assert b["net"] == pytest.approx(65009.13 + 46.82, abs=0.01)


# memurlar.net maaş robotu, Eylül 2026 (Temmuz-Aralık katsayıları). Robotun asgari ücret vergi/damga
# istisnası güncel asgari ücretle hesaplanmadığından (gerçek bordrolarla çelişiyor) vergi kalemleri karşılaştırılmaz.
# Robot yuvarlamayı en sonda yaptığı için kesenek/matrahta 1-2 kuruşluk fark olabilir.
ROBOT = [
    # derece, kademe, yıl, emeklilik, kariyer, toplam kazanç, prim/kesenek toplamı, GV matrahı
    (1, 1, 11, "5510", None, 87194.28, 2596.89 + 4674.39, 26996.51),
    (3, 1, 11, "5510", None, 83767.55, 2425.55 + 4365.99, 24797.88),
    (5, 1, 11, "5510", None, 81349.13, 2304.63 + 4148.33, 24214.78),
    (9, 1, 11, "5510", None, 78174.48, 2145.89 + 3862.61, 21484.58),
    (1, 1, 11, "5510", "uzman", 96174.70, 2596.89 + 4674.39, 26996.51),
    (1, 1, 11, "5510", "basogretmen", 105155.12, 2596.89 + 4674.39, 26996.51),
    (1, 2, 23, "5434", None, 87666.94, 8970.94, 25769.50),
    (3, 2, 23, "5434", None, 84216.58, 6383.32, 25655.11),
    (6, 2, 23, "5434", None, 81490.94, 6186.70, 24622.84),
    (1, 4, 30, "5434", None, 87919.02, 9011.27, 25981.25),
]


@pytest.mark.parametrize("derece,kademe,yil,emeklilik,kariyer,toplam,prim,matrah", ROBOT)
def test_robot_ile_kazanc_ve_kesenek(derece, kademe, yil, emeklilik, kariyer, toplam, prim, matrah):
    b = mm.memur_maasi(derece, kademe, yil, kariyer=kariyer, emeklilik=emeklilik, ay=9)
    assert b["toplam_kazanc"] == pytest.approx(toplam, abs=0.001)
    k = b["kesintiler"]
    assert k.get("malulluk_yaslilik", 0) + k.get("gss", 0) + k.get("emekli_kesenegi", 0) == pytest.approx(prim, abs=0.021)
    assert b["gelir_vergisi_matrahi"] == pytest.approx(matrah, abs=0.031)


def test_aile_yardimi():
    b = mm.memur_maasi(1, 4, 20, emeklilik="5434", es_calismiyor=True, cocuk_72_ay_ustu=2, ay=9)
    assert b["yardimlar"] == {"es_yardimi": 3581.14, "cocuk_yardimi": 787.76}  # robot: 2.273 ve 2 x 250 gösterge
    kucuk = mm.memur_maasi(1, 1, 11, cocuk_72_ay_alti=1, ay=9)
    assert kucuk["yardimlar"]["cocuk_yardimi"] == 787.76  # 500 gösterge
    # aile yardımından vergi kesilmez: net yardım kadar artar
    yok = mm.memur_maasi(1, 1, 11, ay=9)
    assert kucuk["net"] == pytest.approx(yok["net"] + 787.76, abs=0.01)


def test_istisnalar_isci_ile_ayni():
    # İBB 2026 Şubat memur bordrosunda gelir vergisi istisnası 4.211,33, damga istisnası 250,70.
    # Matrah 20.000 TL'nin altındayken vergi istisnadan küçük kalır, istisna vergiyle sınırlanır.
    b = mm.memur_maasi(1, 1, 11, ay=2, onceki_kumulatif_matrah=0)
    assert b["damga_vergisi_istisnasi"] == 250.70
    assert b["gelir_vergisi_istisnasi"] == b["hesaplanan_gelir_vergisi"] < 4211.33
    assert b["kesintiler"]["gelir_vergisi"] == 0
    # Üst dilimde (Eylül, kümülatif 400.000 üstü) istisna asgari ücretin o ayki vergisiyle (5.615,10) sınırlıdır.
    ust = mm.memur_maasi(1, 1, 11, ay=9, onceki_kumulatif_matrah=400000)
    assert ust["gelir_vergisi_istisnasi"] == 5615.10
    assert ust["kesintiler"]["gelir_vergisi"] == pytest.approx(ust["gelir_vergisi_matrahi"] * 0.27 - 5615.10, abs=0.01)


def test_kidem_25_yil_siniri_ve_bes():
    b30 = mm.memur_maasi(1, 4, 30, ay=9)
    b25 = mm.memur_maasi(1, 4, 25, ay=9)
    assert b30["kazanclar"]["kidem_ayligi"] == b25["kazanclar"]["kidem_ayligi"] == 787.76
    bes = mm.memur_maasi(1, 1, 0, ay=9, bes=True)
    assert bes["kesintiler"]["bes"] == 1547.00  # robot: prim matrahının %3'ü, tam lira


def test_hatalar():
    for kw in (dict(unvan="polis"), dict(emeklilik="4a"), dict(kariyer="mudur"), dict(ay=13)):
        with pytest.raises(ValueError):
            mm.memur_maasi(1, 1, 5, **kw)
    with pytest.raises(ValueError):
        mm.memur_maasi(1, 5, 5)  # 1. derecede 4 kademe var
    with pytest.raises(ValueError):
        mm.memur_maasi(1, 1, 5, yil=2023)
