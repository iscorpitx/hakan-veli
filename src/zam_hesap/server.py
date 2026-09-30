"""MCP sunucusu: hesaplama fonksiyonlarını Claude gibi asistanlara araç olarak sunar."""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from . import __version__, emekli, is_hukuku, maas, memur, memur_maas
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
def brutten_nete(
    brut: float,
    ay: int = 1,
    yil: int | None = None,
    onceki_kumulatif_matrah: float | None = None,
    gv_istisna_tutari: float = 0,
    sgdp: bool = False,
    engellilik_derecesi: int | None = None,
    bes: bool = False,
    sendika_aidati: float = 0,
) -> dict[str, Any]:
    """Aylık brüt ücretten net ücreti hesaplar (SGK, işsizlik, gelir ve damga vergisi, asgari ücret istisnası).

    ay: 1-12. Gelir vergisi kümülatif olduğundan yıl içinde ilerledikçe net düşebilir.
    onceki_kumulatif_matrah: önceki aylarda birikmiş gelir vergisi matrahı. Kullanıcının bordrosu varsa
    bordrodaki "kümülatif gelir vergisi matrahı" (bu ay dahil) eksi bu ayın "gelir vergisi matrahı" girilir;
    böylece sonuç bordroyla birebir tutar. Verilmezse yılbaşından beri aynı brüt varsayılır.
    Brüt ücret olarak bordrodaki "SGK matrahı" girilir (ücret + yol parası gibi SGK'ya tabi ödemeler;
    ayni yemek yardımı hariç).
    gv_istisna_tutari: SGK'ya tabi olup gelir vergisinden istisna tutar (ör. yol yardımı istisnası). Bordroda
    gelir vergisi matrahı "SGK matrahı - SGK işçi - işsizlik işçi"den düşükse aradaki fark budur.
    Desteklenen yıllar: guncel_parametreler ile görülebilir (geçmiş bordrolar için 2023 dahil).
    sgdp: emekli olup çalışıyorsa true (SGK yerine %7,5 SGDP, işsizlik primi yok).
    engellilik_derecesi: 1, 2 veya 3 (aylık engellilik indirimi gelir vergisi matrahından düşülür).
    bes: otomatik katılım BES kesintisi varsa true (%3, netten düşülür).
    sendika_aidati: aylık sendika aidatı (TL); gelir vergisi matrahından düşülür ve netten kesilir.
    """
    return maas.brutten_nete(
        brut, ay, yil, onceki_kumulatif_matrah, gv_istisna_tutari, sgdp, engellilik_derecesi, bes, sendika_aidati
    )


@mcp.tool()
def netten_brute(
    net: float,
    ay: int = 1,
    yil: int | None = None,
    onceki_kumulatif_matrah: float | None = None,
    gv_istisna_tutari: float = 0,
    sgdp: bool = False,
    engellilik_derecesi: int | None = None,
    bes: bool = False,
    sendika_aidati: float = 0,
) -> dict[str, Any]:
    """İstenen aylık net ücrete karşılık gelen brüt ücreti bulur.

    onceki_kumulatif_matrah: önceki aylarda birikmiş gelir vergisi matrahı (bilinmiyorsa boş bırak).
    gv_istisna_tutari: SGK'ya tabi olup gelir vergisinden istisna tutar (ör. yol yardımı istisnası).
    sgdp: emekli olup çalışıyorsa true (SGK yerine %7,5 SGDP, işsizlik primi yok).
    engellilik_derecesi: 1, 2 veya 3 (aylık engellilik indirimi gelir vergisi matrahından düşülür).
    bes: otomatik katılım BES kesintisi varsa true (%3, netten düşülür).
    sendika_aidati: aylık sendika aidatı (TL); gelir vergisi matrahından düşülür ve netten kesilir.
    """
    return maas.netten_brute(
        net, ay, yil, onceki_kumulatif_matrah, gv_istisna_tutari, sgdp, engellilik_derecesi, bes, sendika_aidati
    )


@mcp.tool()
def yillik_bordro(
    brut: float,
    yil: int | None = None,
    sgdp: bool = False,
    engellilik_derecesi: int | None = None,
    bes: bool = False,
) -> dict[str, Any]:
    """Aynı brüt ücret için 12 aylık bordro tablosu ve yıllık toplamlar.

    sgdp: emekli olup çalışıyorsa true (SGK yerine %7,5 SGDP, işsizlik primi yok).
    engellilik_derecesi: 1, 2 veya 3 (aylık engellilik indirimi gelir vergisi matrahından düşülür).
    bes: otomatik katılım BES kesintisi varsa true (%3, netten düşülür).
    """
    return maas.yillik_bordro(brut, yil, sgdp, engellilik_derecesi, bes)


@mcp.tool()
def isveren_maliyeti(brut: float, tesvik: str = "yok", yil: int | None = None, sgdp: bool = False) -> dict[str, Any]:
    """Brüt ücretin işverene toplam aylık maliyeti.

    tesvik: "yok" (teşviksiz), "genel" (imalat dışı sektör, 2 puan indirim), "imalat" (5 puan indirim).
    sgdp: emekli çalışan için true (SGDP işveren payı %24,75; teşvik ve işsizlik primi yok).
    """
    return maas.isveren_maliyeti(brut, tesvik, yil, sgdp)


@mcp.tool()
def asgari_ucret(yil: int | None = None) -> dict[str, Any]:
    """Asgari ücretin brüt, net ve işveren maliyeti özeti."""
    return maas.asgari_ucret(yil)


@mcp.tool()
def asgari_ucret_senaryosu(
    zam_oranlari_yuzde: list[float] | None = None,
    yeni_netler: list[float] | None = None,
    yil: int | None = None,
) -> dict[str, Any]:
    """Asgari ücrete zam senaryoları: "%25 zam gelirse net ne olur?" gibi sorular için.

    zam_oranlari_yuzde: bir veya birden çok oran, ör. [20, 25, 30, 35]. Karşılaştırma istenirse hepsini tek çağrıda ver.
    yeni_netler: açıklanan/konuşulan yeni net tutarlar, ör. [35000]. Brüt ve işveren maliyeti bulunur.
    """
    return maas.asgari_ucret_senaryosu(zam_oranlari_yuzde, yeni_netler, yil)


@mcp.tool()
def emekli_zammi(
    mevcut_aylik: float,
    donem: str | None = None,
    zam_orani_yuzde: float | None = None,
    asil_aylik: float | None = None,
) -> dict[str, Any]:
    """SSK/Bağ-Kur emeklisinin zamlı aylığını hesaplar.

    mevcut_aylik: şu an eline geçen aylık.
    donem: "2026-01", "2026-07" gibi. Verilmezse en son dönem.
    zam_orani_yuzde: kayıtlı oran yerine senaryo/tahmin oranı kullanmak için (ör. 15.5).
    asil_aylik: en düşük aylık desteği alanlar için desteksiz asıl aylık. Kullanıcı en düşük aylığı
        alıyorsa (ör. 20.000 TL) asıl aylığını sor; zam asıl aylığa uygulanır.
    """
    return emekli.emekli_zammi(mevcut_aylik, donem, zam_orani_yuzde, asil_aylik)


@mcp.tool()
def emekli_zam_senaryosu(
    mevcut_aylik: float,
    zam_oranlari_yuzde: list[float],
    asil_aylik: float | None = None,
    en_dusuk_aylik: float | None = None,
) -> dict[str, Any]:
    """Gelecek SSK/Bağ-Kur emekli zammı için karşılaştırma: "%10, %15, %20 gelirse ne alırım?"

    Birden çok oranı tek çağrıda ver. asil_aylik: en düşük aylık desteği alanlar için desteksiz aylık.
    en_dusuk_aylik: yeni en düşük aylık biliniyorsa (yoksa aynı oranda artacağı varsayılır).
    Oran bilinmiyorsa önce kumulatif_enflasyon ile aylık enflasyon tahminlerinden hesapla.
    """
    return emekli.emekli_zam_senaryosu(mevcut_aylik, zam_oranlari_yuzde, asil_aylik, en_dusuk_aylik)


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
def memur_zam_senaryosu(
    mevcut_net: float,
    tur: str = "memur",
    zam_oranlari_yuzde: list[float] | None = None,
    toplu_sozlesme_yuzde: float | None = None,
    onceki_toplu_sozlesme_yuzde: float | None = None,
    alti_aylik_enflasyon_yuzde: list[float] | None = None,
) -> dict[str, Any]:
    """Gelecek memur / memur emeklisi (4/c) zammı için karşılaştırma tablosu.

    tur: "memur" veya "emekli".
    zam_oranlari_yuzde: doğrudan toplam oranlar, ör. [10, 15, 20].
    Ya da enflasyon senaryosu: toplu_sozlesme_yuzde (yeni dönem), onceki_toplu_sozlesme_yuzde (biten dönem)
    ve alti_aylik_enflasyon_yuzde (ör. [8, 10, 12]) verilir; enflasyon farkı dahil toplam zam hesaplanır.
    """
    return memur.memur_zam_senaryosu(
        mevcut_net, tur, zam_oranlari_yuzde, toplu_sozlesme_yuzde, onceki_toplu_sozlesme_yuzde, alti_aylik_enflasyon_yuzde
    )


@mcp.tool()
def memur_maasi(
    derece: int,
    kademe: int,
    hizmet_yili: int,
    unvan: str = "ogretmen",
    kariyer: str | None = None,
    emeklilik: str = "5510",
    es_calismiyor: bool = False,
    cocuk_72_ay_alti: int = 0,
    cocuk_72_ay_ustu: int = 0,
    ay: int = 7,
    yil: int | None = None,
    onceki_kumulatif_matrah: float | None = None,
    sendika_aidati: float = 0,
    bes: bool = False,
) -> dict[str, Any]:
    """Unvana göre memur maaşı: kalem kalem kazançlar, kesintiler ve net (şimdilik unvan: "ogretmen").

    derece/kademe: kazanılmış hak aylığı (ör. 7/1). hizmet_yili: kıdem yılı.
    kariyer: None, "uzman" (uzman öğretmen) veya "basogretmen".
    emeklilik: "5510" (2008 ve sonrası göreve başlayan) veya "5434" (2008 öncesi, Emekli Sandığı).
    es_calismiyor: eş çalışmıyorsa aile yardımı ödenir. cocuk_72_ay_alti / cocuk_72_ay_ustu: çocuk sayıları.
    ay: maaş ayı (1-6 Ocak-Haziran, 7-12 Temmuz-Aralık katsayıları; vergi dilimi ve istisna için de kullanılır).
    onceki_kumulatif_matrah: bordrodaki "geçen aylar vergi matrahı toplamı" (bilinmiyorsa boş).
    Ek ders, fazla mesai, dil/makam tazminatı gibi kişiye özel ödemeler dahil değildir.
    """
    return memur_maas.memur_maasi(
        derece, kademe, hizmet_yili, unvan, kariyer, emeklilik, es_calismiyor, cocuk_72_ay_alti,
        cocuk_72_ay_ustu, ay, yil, onceki_kumulatif_matrah, sendika_aidati, bes,
    )


@mcp.tool()
def kidem_tazminati(giydirilmis_brut: float, giris: str, cikis: str, tavan: float | None = None) -> dict[str, Any]:
    """Kıdem tazminatı. Tarihler YYYY-AA-GG. giydirilmis_brut: son brüt ücret + düzenli yan ödemeler
    (yemek, yol, ikramiyenin aylık payı vb.). Tavan çıkış tarihine göre uygulanır; yalnızca damga vergisi kesilir.
    tavan: kayıtlı olmayan ileri tarihli çıkışlar veya senaryo için tahmini tavan (tavan her dönem memur zammı
    oranında artar).
    """
    return is_hukuku.kidem_tazminati(giydirilmis_brut, giris, cikis, tavan)


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
