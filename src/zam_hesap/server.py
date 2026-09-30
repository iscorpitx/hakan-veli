"""MCP sunucusu: hesaplama fonksiyonlarını Claude gibi asistanlara araç olarak sunar."""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from . import __version__, emekli, is_hukuku, maas, memur
from .parametreler import desteklenen_yillar, yukle

mcp = MCPServer(
    "zam-hesap",
    version=__version__,
    instructions=(
        "Türkiye'de maaş, asgari ücret, emekli/memur zammı, kıdem-ihbar tazminatı, izin ve mesai hesapları. Rakamları tahmin etme; "
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
def memur_zammi(
    mevcut_net: float, tur: str = "memur", donem: str | None = None, zam_orani_yuzde: float | None = None
) -> dict[str, Any]:
    """Memur maaşına veya memur emeklisi (4/c, Emekli Sandığı) aylığına dönemin zammını uygular.

    tur: "memur" veya "emekli". donem: "2026-01", "2026-07" gibi; verilmezse en son dönem.
    zam_orani_yuzde: senaryo/tahmin oranı (ör. 11.5).
    """
    return memur.memur_zammi(mevcut_net, tur, donem, zam_orani_yuzde)


@mcp.tool()
def kidem_tazminati(giydirilmis_brut: float, giris: str, cikis: str) -> dict[str, Any]:
    """Kıdem tazminatı. Tarihler YYYY-AA-GG. giydirilmis_brut: son brüt ücret + düzenli yan ödemeler
    (yemek, yol, ikramiyenin aylık payı vb.). Tavan çıkış tarihine göre uygulanır; yalnızca damga vergisi kesilir.
    """
    return is_hukuku.kidem_tazminati(giydirilmis_brut, giris, cikis)


@mcp.tool()
def ihbar_tazminati(
    giydirilmis_brut: float, giris: str, cikis: str, onceki_kumulatif_matrah: float = 0
) -> dict[str, Any]:
    """İhbar tazminatı ve ihbar süresi (2/4/6/8 hafta). Tarihler YYYY-AA-GG.

    onceki_kumulatif_matrah: çıkış yılında o ana kadarki gelir vergisi matrahı (bilinmiyorsa 0).
    """
    return is_hukuku.ihbar_tazminati(giydirilmis_brut, giris, cikis, onceki_kumulatif_matrah)


@mcp.tool()
def hizmet_suresi(giris: str, cikis: str) -> dict[str, Any]:
    """İki tarih arasındaki çalışma süresi (yıl, ay, gün). Tarihler YYYY-AA-GG."""
    return is_hukuku.hizmet_suresi(giris, cikis)


@mcp.tool()
def yillik_izin(hizmet_yili: int, yas: int | None = None, yeralti: bool = False) -> dict[str, Any]:
    """Yıllık ücretli izin gün sayısı (1-5 yıl 14, 5-15 yıl 20, 15+ yıl 26 gün; yaş ve yer altı kuralları dahil)."""
    return is_hukuku.yillik_izin(hizmet_yili, yas, yeralti)


@mcp.tool()
def izin_ucreti(brut: float, gun: int, yil: int | None = None, onceki_kumulatif_matrah: float = 0) -> dict[str, Any]:
    """Kullanılmayan yıllık izin ücreti (işten ayrılırken ödenir), brüt ve net."""
    return is_hukuku.izin_ucreti(brut, gun, yil, onceki_kumulatif_matrah)


@mcp.tool()
def fazla_mesai(brut: float, saat: float, tur: str = "fazla_calisma") -> dict[str, Any]:
    """Fazla mesai brüt ücreti. tur: "fazla_calisma" (%50 zamlı) veya "fazla_surelerle" (%25 zamlı)."""
    return is_hukuku.fazla_mesai(brut, saat, tur)


@mcp.tool()
def tatil_mesaisi(brut: float, gun: float) -> dict[str, Any]:
    """Ulusal bayram / genel tatil gününde çalışma için ek ödeme (her gün için 1 günlük brüt ücret)."""
    return is_hukuku.tatil_mesaisi(brut, gun)


@mcp.tool()
def tis_zammi(
    mevcut_brut: float,
    zam_oranlari_yuzde: list[float],
    seyyanen_brut: float = 0,
    ay: int = 1,
    yil: int | None = None,
) -> dict[str, Any]:
    """Toplu iş sözleşmesi zammı (belediye, kamu veya özel sektör işçisi): yeni brüt ve net ücret.

    zam_oranlari_yuzde: sırayla uygulanacak oranlar, ör. [10, 6]. seyyanen_brut: oranlardan önce eklenen sabit tutar.
    """
    return is_hukuku.tis_zammi(mevcut_brut, zam_oranlari_yuzde, seyyanen_brut, ay, yil)


@mcp.tool()
def kamu_isci_protokolu(yil: int | None = None) -> dict[str, Any]:
    """Kamu işçileri toplu iş sözleşmesi çerçeve protokolündeki dönemsel zam oranları."""
    return is_hukuku.kamu_isci_protokolu(yil)


@mcp.tool()
def guncel_parametreler(yil: int | None = None) -> dict[str, Any]:
    """Hesaplarda kullanılan oranlar, tutarlar ve kaynakları."""
    return {"desteklenen_yillar": desteklenen_yillar(), **yukle(yil)}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
