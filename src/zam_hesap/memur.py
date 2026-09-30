"""Memur ve memur emeklisi (4/c, Emekli Sandığı) zammı."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from .maas import yuvarla
from .parametreler import d, yukle

TURLER = ("memur", "emekli")


def memur_zammi(
    mevcut_net: float,
    tur: str = "memur",
    donem: str | None = None,
    zam_orani_yuzde: float | None = None,
) -> dict[str, Any]:
    """Memur maaşına veya memur emeklisi (4/c) aylığına dönemin zammını uygular.

    Not: Zam, maaşın tüm kalemlerine aynı oranda yansıdığı varsayımıyla yaklaşık hesaplanır.
    Kişiye özel kalemler (aile/çocuk yardımı, vergi dilimi) nedeniyle gerçek tutar birkaç yüz TL
    farklı olabilir.
    """
    if tur not in TURLER:
        raise ValueError(f"tur şunlardan biri olmalı: {TURLER}")
    maas = d(mevcut_net)
    if maas <= 0:
        raise ValueError("mevcut_net pozitif olmalı")

    if donem is None:
        donem = max(yukle()["memur"]["donemler"])
    try:
        donemler = yukle(int(donem.split("-")[0])).get("memur", {}).get("donemler", {})
    except ValueError:
        donemler = {}
    kayit = donemler.get(donem, {})
    senaryo = zam_orani_yuzde is not None
    if not kayit and not senaryo:
        raise ValueError(f"{donem} dönemi için kayıtlı oran yok; zam_orani_yuzde verin. Kayıtlı dönemler: {sorted(donemler)}")

    oran = d(zam_orani_yuzde) / 100 if senaryo else d(kayit["zam_orani"])
    zamli = yuvarla(maas * (1 + oran))
    sonuc: dict[str, Any] = {
        "tur": tur,
        "donem": donem,
        "mevcut_net": float(maas),
        "zam_orani_yuzde": float(oran * 100),
        "zam_tutari": float(zamli - maas),
        "zamli_net": float(zamli),
        "kaynak": "kullanıcı senaryosu" if senaryo else kayit["kaynak"],
    }
    if senaryo:
        return sonuc

    notlar = []
    if tur == "memur":
        if "taban_aylik_artisi" in kayit:
            notlar.append(
                f"Bu dönemde brüt taban aylığa ayrıca {kayit['taban_aylik_artisi']:.0f} TL eklendi; "
                "net maaşa etkisi kişiye göre değişir ve bu hesaba dahil değildir."
            )
        if "en_dusuk_memur_maasi" in kayit:
            sonuc["en_dusuk_memur_maasi"] = float(kayit["en_dusuk_memur_maasi"])
    else:
        en_dusuk = kayit.get("en_dusuk_emekli_aylik")
        if en_dusuk is not None:
            sonuc["en_dusuk_emekli_aylik"] = float(en_dusuk)
            if zamli < d(en_dusuk):
                sonuc["zamli_net"] = float(en_dusuk)
                notlar.append("Zamlı aylık en düşük memur emekli aylığının altında kaldığı için bu tutara tamamlanır.")
    if notlar:
        sonuc["not"] = " ".join(notlar)
    return sonuc


def _memur_zam_orani(toplu_sozlesme_yuzde: float, alti_aylik_enflasyon_yuzde: float, onceki_toplu_sozlesme_yuzde: float) -> dict[str, float]:
    """Memur zammı = toplu sözleşme zammı ile enflasyon farkının bileşiği.

    Enflasyon farkı = (1 + 6 aylık enflasyon) / (1 + önceki dönemin toplu sözleşme zammı) - 1; negatifse 0.
    Örnek (Temmuz 2026): önceki %11, enflasyon %17,76 -> fark %6,09; yeni dönem %7 -> toplam %13,52.
    """
    ts = d(toplu_sozlesme_yuzde) / 100
    fark = max(Decimal(0), (1 + d(alti_aylik_enflasyon_yuzde) / 100) / (1 + d(onceki_toplu_sozlesme_yuzde) / 100) - 1)
    toplam = (1 + ts) * (1 + fark) - 1
    return {
        "toplu_sozlesme_yuzde": float(toplu_sozlesme_yuzde),
        "enflasyon_farki_yuzde": float(yuvarla(fark * 100)),
        "toplam_zam_yuzde": float(yuvarla(toplam * 100)),
        "_toplam": toplam,
    }


def memur_zam_senaryosu(
    mevcut_net: float,
    tur: str = "memur",
    zam_oranlari_yuzde: list[float] | None = None,
    toplu_sozlesme_yuzde: float | None = None,
    onceki_toplu_sozlesme_yuzde: float | None = None,
    alti_aylik_enflasyon_yuzde: list[float] | None = None,
) -> dict[str, Any]:
    """Gelecek memur / memur emeklisi zammı için karşılaştırma tablosu.

    İki kullanım:
    - zam_oranlari_yuzde: doğrudan toplam oranlar, ör. [10, 15, 20].
    - toplu_sozlesme_yuzde + onceki_toplu_sozlesme_yuzde + alti_aylik_enflasyon_yuzde: enflasyon
      senaryolarından toplam zammı hesaplar (enflasyon farkı dahil).
    """
    if tur not in TURLER:
        raise ValueError(f"tur şunlardan biri olmalı: {TURLER}")
    maas = d(mevcut_net)
    if maas <= 0:
        raise ValueError("mevcut_net pozitif olmalı")

    satirlar: list[dict[str, Any]] = []
    for oran in zam_oranlari_yuzde or []:
        satirlar.append({"toplam_zam_yuzde": float(oran), "_toplam": d(oran) / 100})
    if alti_aylik_enflasyon_yuzde:
        if toplu_sozlesme_yuzde is None or onceki_toplu_sozlesme_yuzde is None:
            raise ValueError("enflasyon senaryosu için toplu_sozlesme_yuzde ve onceki_toplu_sozlesme_yuzde gerekli")
        for enf in alti_aylik_enflasyon_yuzde:
            satir = _memur_zam_orani(toplu_sozlesme_yuzde, enf, onceki_toplu_sozlesme_yuzde)
            satirlar.append({"alti_aylik_enflasyon_yuzde": float(enf), **satir})
    if not satirlar:
        raise ValueError("zam_oranlari_yuzde veya enflasyon senaryosu verilmeli")

    senaryolar = []
    for satir in satirlar:
        toplam = satir.pop("_toplam")
        zamli = yuvarla(maas * (1 + toplam))
        senaryolar.append({**satir, "zamli_net": float(zamli), "artis": float(zamli - maas)})
    return {
        "tur": tur,
        "mevcut_net": float(maas),
        "senaryolar": senaryolar,
        "not": "Tahmindir. Zam, net maaşın tüm kalemlerine aynı oranda yansıtılarak yaklaşık hesaplanır.",
    }
