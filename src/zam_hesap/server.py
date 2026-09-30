"""MCP sunucusu: hesaplama fonksiyonlarını Claude gibi asistanlara araç olarak sunar."""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from . import __version__, emekli, maas
from .parametreler import desteklenen_yillar, yukle

mcp = MCPServer(
    "zam-hesap",
    version=__version__,
    instructions=(
        "Türkiye'de maaş, asgari ücret ve emekli zammı hesapları. Rakamları tahmin etme; "
        "bu araçları çağır ve sonuçları kuruşuyla aktar. Sonuçlar bilgilendirme amaçlıdır."
    ),
)


@mcp.tool()
def brutten_nete(brut: float, ay: int = 1, yil: int | None = None) -> dict[str, Any]:
    """Aylık brüt ücretten net ücreti hesaplar (SGK, işsizlik, gelir ve damga vergisi, asgari ücret istisnası).

    ay: 1-12. Gelir vergisi kümülatif olduğundan yıl içinde ilerledikçe net düşebilir.
    Yılbaşından beri aynı brüt ücretin alındığı varsayılır.
    """
    return maas.brutten_nete(brut, ay, yil)


@mcp.tool()
def netten_brute(net: float, ay: int = 1, yil: int | None = None) -> dict[str, Any]:
    """İstenen aylık net ücrete karşılık gelen brüt ücreti bulur."""
    return maas.netten_brute(net, ay, yil)


@mcp.tool()
def yillik_bordro(brut: float, yil: int | None = None) -> dict[str, Any]:
    """Aynı brüt ücret için 12 aylık bordro tablosu ve yıllık toplamlar."""
    return maas.yillik_bordro(brut, yil)


@mcp.tool()
def isveren_maliyeti(brut: float, tesvik: str = "yok", yil: int | None = None) -> dict[str, Any]:
    """Brüt ücretin işverene toplam aylık maliyeti.

    tesvik: "yok" (teşviksiz), "genel" (imalat dışı sektör, 2 puan indirim), "imalat" (5 puan indirim).
    """
    return maas.isveren_maliyeti(brut, tesvik, yil)


@mcp.tool()
def asgari_ucret(yil: int | None = None) -> dict[str, Any]:
    """Asgari ücretin brüt, net ve işveren maliyeti özeti."""
    return maas.asgari_ucret(yil)


@mcp.tool()
def emekli_zammi(
    mevcut_aylik: float, donem: str | None = None, zam_orani_yuzde: float | None = None
) -> dict[str, Any]:
    """SSK/Bağ-Kur emeklisinin zamlı aylığını hesaplar.

    donem: "2026-01", "2026-07" gibi. Verilmezse en son dönem.
    zam_orani_yuzde: kayıtlı oran yerine senaryo/tahmin oranı kullanmak için (ör. 15.5).
    """
    return emekli.emekli_zammi(mevcut_aylik, donem, zam_orani_yuzde)


@mcp.tool()
def kumulatif_enflasyon(aylik_oranlar_yuzde: list[float]) -> dict[str, Any]:
    """Aylık enflasyon oranlarından (yüzde) birikimli artışı hesaplar. Emekli zammı tahmini için kullanılır."""
    return emekli.kumulatif_enflasyon(aylik_oranlar_yuzde)


@mcp.tool()
def guncel_parametreler(yil: int | None = None) -> dict[str, Any]:
    """Hesaplarda kullanılan oranlar, tutarlar ve kaynakları."""
    return {"desteklenen_yillar": desteklenen_yillar(), **yukle(yil)}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
