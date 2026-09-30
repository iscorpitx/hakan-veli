"""Memur ve memur emeklisi (4/c, Emekli Sandığı) zammı."""

from __future__ import annotations

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
        donemler = yukle(int(donem.split("-")[0]))["memur"]["donemler"]
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
