import asyncio

from zam_hesap.server import mcp

BEKLENEN_ARACLAR = {
    "brutten_nete",
    "netten_brute",
    "yillik_bordro",
    "isveren_maliyeti",
    "asgari_ucret",
    "asgari_ucret_senaryosu",
    "emekli_zammi",
    "kumulatif_enflasyon",
    "guncel_parametreler",
    "memur_zammi",
    "memur_maasi",
    "memur_zam_senaryosu",
    "emekli_zam_senaryosu",
    "kidem_tazminati",
    "ihbar_tazminati",
    "hizmet_suresi",
    "yillik_izin",
    "izin_ucreti",
    "fazla_mesai",
    "tatil_mesaisi",
    "tis_zammi",
    "kamu_isci_protokolu",
}


def test_araclar_kayitli():
    araclar = asyncio.run(mcp.list_tools())
    assert {a.name for a in araclar} == BEKLENEN_ARACLAR


def test_arac_cagrisi():
    sonuc = asyncio.run(mcp.call_tool("asgari_ucret", {}))
    assert "28075.5" in str(sonuc)
