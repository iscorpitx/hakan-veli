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


def test_gercek_bordro_kasim_2023():
    # Gerçek bir işyeri bordrosundan (Kasım 2023) yalnızca tutarlar; kişisel bilgi içermez.
    # Ücret kazançları toplamı 20.328,30 TL (ayni yemek yardımı hariç), bordrodaki kümülatif
    # gelir vergisi matrahı 160.107,36 TL (bu ay dahil).
    b = maas.brutten_nete(20328.30, 11, 2023, onceki_kumulatif_matrah=160107.36 - 17279.06)
    assert b["sgk_isci"] == 2845.96
    assert b["issizlik_isci"] == 203.28
    assert b["gelir_vergisi_matrahi"] == 17279.06
    assert b["kumulatif_matrah"] == 160107.36
    assert b["odenecek_gelir_vergisi"] == 1882.87
    assert b["odenecek_damga_vergisi"] == 52.47
    assert b["net"] == 15343.72  # bordrodaki "net ödenecek tutar"


@pytest.mark.parametrize("ay,brut,net", [(1, 10008.00, 8506.80), (6, 10008.00, 8506.80), (7, 13414.50, 11402.32), (12, 13414.50, 11402.32)])
def test_2023_asgari_ucret_yil_ici_artis(ay, brut, net):
    b = maas.brutten_nete(brut, ay, 2023)
    assert b["odenecek_gelir_vergisi"] == 0
    assert b["odenecek_damga_vergisi"] == 0
    assert b["net"] == net


def test_2023_asgari_ucret_isveren_maliyeti():
    # 2023 Temmuz-Aralık: %20,5 - 5 puan + %2 işsizlik
    assert maas.asgari_ucret(2023)["isveren_maliyeti"]["genel"] == 15762.04
    assert maas.isveren_maliyeti(10008, "genel", 2023)["toplam_maliyet"] == 11759.40


def test_onceki_kumulatif_matrah_vergi_dilimini_degistirir():
    varsayilan = maas.brutten_nete(60000, 3, 2026)
    yuksek = maas.brutten_nete(60000, 3, 2026, onceki_kumulatif_matrah=380000)
    assert yuksek["hesaplanan_gelir_vergisi"] > varsayilan["hesaplanan_gelir_vergisi"]
    assert yuksek["net"] < varsayilan["net"]
    with pytest.raises(ValueError):
        maas.brutten_nete(60000, 3, 2026, onceki_kumulatif_matrah=-1)


def test_netten_brute_onceki_kumulatif_ile():
    b = maas.brutten_nete(20328.30, 11, 2023, onceki_kumulatif_matrah=142828.30)
    geri = maas.netten_brute(b["net"], 11, 2023, onceki_kumulatif_matrah=142828.30)
    assert geri["brut"] == pytest.approx(20328.30, abs=0.02)


def test_2023_verisi_olmayan_araclar_anlasilir_hata_verir():
    from zam_hesap import is_hukuku, memur

    with pytest.raises(ValueError):
        memur.memur_zammi(40000, "memur", "2023-07")
    with pytest.raises(ValueError, match="tavan"):
        is_hukuku.kidem_tazminati(30000, "2020-01-01", "2023-11-30")
    with pytest.raises(ValueError):
        is_hukuku.kamu_isci_protokolu(2023)


def test_gercek_bordro_agustos_2026():
    # Gerçek bir işyeri bordrosundan (Ağustos 2026) yalnızca tutarlar; kişisel bilgi içermez.
    # SGK matrahı 55.094,02 (ücret + yol parası), yol yardımının 4.942,13 TL'si gelir vergisinden istisna,
    # kümülatif gelir vergisi matrahı 325.311,52 (bu ay dahil).
    b = maas.brutten_nete(55094.02, 8, 2026, onceki_kumulatif_matrah=325311.52 - 41887.79, gv_istisna_tutari=4942.13)
    assert b["sgk_isci"] == 7713.16
    assert b["issizlik_isci"] == 550.94
    assert b["gelir_vergisi_matrahi"] == 41887.79
    assert b["kumulatif_matrah"] == 325311.52
    assert b["gelir_vergisi_istisnasi"] == 5615.10  # Ağustos 2026 asgari ücret istisnası
    assert b["odenecek_gelir_vergisi"] == 2762.46
    assert b["odenecek_damga_vergisi"] == 167.46
    assert b["net"] == 43900.00  # bordrodaki "net ödenecek tutar"


def test_gercek_bordro_agustos_2026_netten_brute():
    b = maas.netten_brute(43900, 8, 2026, onceki_kumulatif_matrah=283423.73, gv_istisna_tutari=4942.13)
    assert b["brut"] == 55094.02


def test_gv_istisna_tutari():
    normal = maas.brutten_nete(60000, 1, 2026)
    istisnali = maas.brutten_nete(60000, 1, 2026, gv_istisna_tutari=5000)
    assert istisnali["sgk_isci"] == normal["sgk_isci"]  # SGK etkilenmez
    assert istisnali["odenecek_damga_vergisi"] == normal["odenecek_damga_vergisi"]  # damga etkilenmez
    assert istisnali["gelir_vergisi_matrahi"] == normal["gelir_vergisi_matrahi"] - 5000
    assert istisnali["net"] == pytest.approx(normal["net"] + 750, abs=0.01)  # %15 dilimde
    with pytest.raises(ValueError):
        maas.brutten_nete(60000, 1, 2026, gv_istisna_tutari=-1)
