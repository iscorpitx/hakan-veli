import asyncio

from zam_hesap.server import mcp

BEKLENEN_ARACLAR = {
    "brutten_nete",
    "netten_brute",
    "yillik_bordro",
    "isveren_maliyeti",
    "asgari_ucret",
    "emekli_zammi",
    "kumulatif_enflasyon",
    "guncel_parametreler",
}


def test_araclar_kayitli():
    araclar = asyncio.run(mcp.list_tools())
    assert {a.name for a in araclar} == BEKLENEN_ARACLAR


def test_arac_cagrisi():
    sonuc = asyncio.run(mcp.call_tool("asgari_ucret", {}))
    assert "28075.5" in str(sonuc)
