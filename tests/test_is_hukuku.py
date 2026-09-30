import pytest

from zam_hesap import is_hukuku as h


@pytest.mark.parametrize(
    "giris,cikis,beklenen",
    [
        ("2020-03-15", "2026-08-10", (6, 4, 26)),
        ("2024-01-31", "2024-02-29", (0, 1, 0)),  # ayın son günü
        ("2025-01-01", "2026-01-01", (1, 0, 0)),
        ("2026-05-10", "2026-05-10", (0, 0, 0)),
    ],
)
def test_hizmet_suresi(giris, cikis, beklenen):
    s = h.hizmet_suresi(giris, cikis)
    assert (s["yil"], s["ay"], s["gun"]) == beklenen


def test_hizmet_suresi_ters_tarih():
    with pytest.raises(ValueError):
        h.hizmet_suresi("2026-01-01", "2025-01-01")


def test_kidem_tam_yillar_tavan_alti():
    s = h.kidem_tazminati(50000, "2021-02-01", "2026-02-01")
    assert s["brut_tazminat"] == 250000.00
    assert s["damga_vergisi"] == 1897.50  # yalnızca damga vergisi
    assert s["net_tazminat"] == 248102.50


def test_kidem_tavan_donemleri():
    ilk = h.kidem_tazminati(100000, "2020-01-01", "2026-06-30")
    ikinci = h.kidem_tazminati(100000, "2020-01-01", "2026-07-01")
    assert ilk["tavan"] == 64948.77
    assert ikinci["tavan"] == 73729.87
    assert ikinci["esas_ucret"] == 73729.87
    assert "tavan" in ikinci["not"]


def test_kidem_kusurat():
    # 2 yıl 6 ay: 2,5 aylık ücret
    s = h.kidem_tazminati(40000, "2024-01-15", "2026-07-15")
    assert s["brut_tazminat"] == 100000.00


def test_kidem_bir_yildan_az():
    s = h.kidem_tazminati(50000, "2025-12-01", "2026-08-10")
    assert s["brut_tazminat"] == 0


@pytest.mark.parametrize(
    "giris,cikis,gun",
    [
        ("2026-03-01", "2026-08-01", 14),
        ("2025-08-01", "2026-08-01", 28),
        ("2024-08-01", "2026-08-01", 42),
        ("2023-08-01", "2026-08-01", 56),
    ],
)
def test_ihbar_sureleri(giris, cikis, gun):
    assert h.ihbar_tazminati(30000, giris, cikis)["ihbar_suresi_gun"] == gun


def test_ihbar_tutari_ve_vergisi():
    s = h.ihbar_tazminati(45000, "2020-01-01", "2026-03-01")
    assert s["brut_tazminat"] == 84000.00  # 1500 x 56
    assert s["gelir_vergisi"] == 12600.00  # %15
    assert s["damga_vergisi"] == 637.56
    assert s["net_tazminat"] == 70762.44


def test_ihbar_ust_dilim():
    s = h.ihbar_tazminati(45000, "2020-01-01", "2026-03-01", onceki_kumulatif_matrah=400000)
    assert s["gelir_vergisi"] == 22680.00  # %27


@pytest.mark.parametrize(
    "yil,yas,yeralti,gun",
    [(0, None, False, 0), (1, None, False, 14), (5, None, False, 14), (6, None, False, 20),
     (15, None, False, 26), (3, 17, False, 20), (3, 55, False, 20), (20, 55, False, 26), (3, None, True, 18)],
)
def test_yillik_izin(yil, yas, yeralti, gun):
    assert h.yillik_izin(yil, yas, yeralti)["izin_gun"] == gun


def test_izin_ucreti():
    s = h.izin_ucreti(45000, 10, 2026)
    assert s["brut"] == 15000.00
    assert s["sgk_isci"] == 2100.00
    assert s["issizlik_isci"] == 150.00
    assert s["gelir_vergisi"] == 1912.50
    assert s["damga_vergisi"] == 113.85
    assert s["net"] == 10723.65


def test_fazla_mesai():
    assert h.fazla_mesai(45000, 10)["fazla_mesai_brut"] == 3000.00
    assert h.fazla_mesai(45000, 10, "fazla_surelerle")["fazla_mesai_brut"] == 2500.00
    with pytest.raises(ValueError):
        h.fazla_mesai(45000, 10, "yanlis")


def test_tatil_mesaisi():
    assert h.tatil_mesaisi(45000, 2)["ek_odeme_brut"] == 3000.00


def test_tis_zammi_bilesik_ve_seyyanen():
    s = h.tis_zammi(40000, [10, 6], seyyanen_brut=1000, yil=2026)
    assert s["yeni_brut"] == 47806.00  # (40000 + 1000) x 1,10 x 1,06
    assert s["yeni_net"] > s["mevcut_net"]


def test_kamu_isci_protokolu():
    p = h.kamu_isci_protokolu(2026)
    assert p["donemler"]["2026-01"]["zam_orani"] == 0.10
    assert p["donemler"]["2026-07"]["zam_orani"] == 0.06


def test_kidem_ileri_tarih_tahmini_tavan():
    s = h.kidem_tazminati(90000, "2020-03-01", "2027-03-01", tavan=80000)
    assert s["tavan_kaynagi"] == "kullanıcı tahmini"
    assert s["brut_tazminat"] == 560000.00  # 7 yıl x 80.000


def test_kidem_ileri_tarih_tavansiz_hata():
    with pytest.raises(ValueError, match="tavan"):
        h.kidem_tazminati(90000, "2020-03-01", "2027-03-01")


def test_kidem_tavan_senaryosu_kayitli_donemde():
    s = h.kidem_tazminati(100000, "2020-01-01", "2026-01-01", tavan=70000)
    assert s["esas_ucret"] == 70000.00
