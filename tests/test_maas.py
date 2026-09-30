import pytest

from zam_hesap import maas


def test_asgari_ucret_2026_resmi_rakamlar():
    # Yayımlanan 2026 asgari ücret tabloları: net 28.075,50; işveren maliyeti 40.874,63 / 40.214,03 / 39.223,13
    s = maas.asgari_ucret(2026)
    assert s["brut"] == 33030.00
    assert s["net"] == 28075.50
    assert s["sgk_isci"] == 4624.20
    assert s["issizlik_isci"] == 330.30
    assert s["isveren_maliyeti"] == {"yok": 40874.63, "genel": 40214.03, "imalat": 39223.13}


@pytest.mark.parametrize("ay", range(1, 13))
def test_asgari_ucret_her_ay_vergisiz(ay):
    b = maas.brutten_nete(33030, ay, 2026)
    assert b["odenecek_gelir_vergisi"] == 0
    assert b["odenecek_damga_vergisi"] == 0
    assert b["net"] == 28075.50


def test_ocak_50000_brut():
    b = maas.brutten_nete(50000, 1, 2026)
    assert b["gelir_vergisi_matrahi"] == 42500.00
    assert b["hesaplanan_gelir_vergisi"] == 6375.00  # %15
    assert b["gelir_vergisi_istisnasi"] == 4211.33  # 28.075,50 x %15
    assert b["odenecek_damga_vergisi"] == 128.80  # 379,50 - 250,70
    assert b["net"] == 40207.53


def test_temmuz_asgari_istisnasi_dilim_gecisi():
    # Asgari ücret matrahı 7. ayda 190.000 TL'lik ilk dilimi aşar.
    b = maas.brutten_nete(33030, 7, 2026)
    assert b["gelir_vergisi_istisnasi"] == 4537.75


def test_gelir_vergisi_tarifesi_dilim_sinirlari():
    dilimler = maas.yukle(2026)["gelir_vergisi"]["ucret_dilimleri"]
    gv = lambda m: float(maas.gelir_vergisi(maas.d(m), dilimler))
    assert gv(190000) == 28500
    assert gv(400000) == 70500
    assert gv(1500000) == 367500
    assert gv(5300000) == 1697500
    assert gv(6300000) == 1697500 + 400000


def test_sgk_tavani():
    b = maas.brutten_nete(400000, 1, 2026)
    assert b["sgk_isci"] == round(33030 * 9 * 0.14, 2)
    m = maas.isveren_maliyeti(400000, "yok", 2026)
    assert m["sgk_isveren"] == 64656.23  # 297.270 x %21,75 = 64.656,225 -> yukarı yuvarlanır


def test_net_yil_icinde_degisir():
    netler = [a["net"] for a in maas.yillik_bordro(100000, 2026)["aylar"]]
    assert netler[0] > netler[-1]  # kümülatif matrah üst dilimlere çıktıkça net düşer
    # Temmuz'da asgari ücret istisnası da üst dilime geçtiği için net Haziran'a göre artabilir.
    assert netler[6] > netler[5]


@pytest.mark.parametrize("brut", [33030, 45000, 87654.32, 150000, 400000])
@pytest.mark.parametrize("ay", [1, 6, 12])
def test_netten_brute_tersine_cevirir(brut, ay):
    net = maas.brutten_nete(brut, ay, 2026)["net"]
    assert maas.netten_brute(net, ay, 2026)["net"] == pytest.approx(net, abs=0.01)


def test_hatali_girdiler():
    with pytest.raises(ValueError):
        maas.brutten_nete(20000, 1, 2026)
    with pytest.raises(ValueError):
        maas.brutten_nete(50000, 13, 2026)
    with pytest.raises(ValueError):
        maas.isveren_maliyeti(50000, "bilinmeyen", 2026)
    with pytest.raises(ValueError):
        maas.brutten_nete(50000, 1, 1999)


def test_asgari_ucret_senaryosu_oranlar():
    s = maas.asgari_ucret_senaryosu([25, 30], yil=2026)
    assert s["mevcut"] == {"brut": 33030.00, "net": 28075.50}
    yuzde25, yuzde30 = s["senaryolar"]
    assert yuzde25["brut"] == 41287.50
    assert yuzde25["net"] == 35094.37  # 41.287,50 - 5.780,25 SGK - 412,88 işsizlik
    assert yuzde25["net_artis"] == 7018.87
    assert yuzde25["isveren_maliyeti_tesviksiz"] == 51093.28
    assert yuzde30["brut"] == 42939.00


def test_asgari_ucret_senaryosu_net_tutar():
    s = maas.asgari_ucret_senaryosu(yeni_netler=[35000], yil=2026)
    sen = s["senaryolar"][0]
    assert sen["net"] == pytest.approx(35000, abs=0.01)
    assert sen["brut"] == 41176.47
    assert sen["zam_orani_yuzde"] == 24.66


def test_asgari_ucret_senaryosu_mevcut_ile_tutarli():
    # %0 senaryosu, bordro hesabıyla aynı neti vermeli
    sen = maas.asgari_ucret_senaryosu([0], yil=2026)["senaryolar"][0]
    assert sen["net"] == maas.asgari_ucret(2026)["net"]
    assert sen["isveren_maliyeti_tesviksiz"] == maas.asgari_ucret(2026)["isveren_maliyeti"]["yok"]


def test_asgari_ucret_senaryosu_bos():
    with pytest.raises(ValueError):
        maas.asgari_ucret_senaryosu()
