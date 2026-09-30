"""SSK (4/a) ve Bağ-Kur (4/b) emekli zammı hesapları."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from .maas import yuvarla
from .parametreler import d, yukle


def kumulatif_enflasyon(aylik_oranlar_yuzde: list[float]) -> dict[str, Any]:
    """Aylık TÜFE değişimlerinden (yüzde) birikimli artışı hesaplar.

    Not: TÜİK'in resmi 6 aylık oranı endeks değerlerinden hesaplanır; aylık oranların
    yuvarlanmış olması nedeniyle burada küçük (~0,01 puan) farklar çıkabilir.
    """
    carpan = Decimal(1)
    for oran in aylik_oranlar_yuzde:
        carpan *= 1 + d(oran) / 100
    return {
        "aylik_oranlar_yuzde": aylik_oranlar_yuzde,
        "kumulatif_yuzde": float((carpan - 1) * 100),
        "kumulatif_yuzde_yuvarlanmis": float(yuvarla((carpan - 1) * 100)),
    }


def emekli_zammi(
    mevcut_aylik: float,
    donem: str | None = None,
    zam_orani_yuzde: float | None = None,
) -> dict[str, Any]:
    """Mevcut aylığa dönemin zammını uygular.

    donem: "YYYY-01" veya "YYYY-07". Verilmezse en son kayıtlı dönem kullanılır.
    zam_orani_yuzde: verilirse kayıtlı oran yerine bu oran kullanılır (tahmin/senaryo için).
    """
    aylik = d(mevcut_aylik)
    if aylik <= 0:
        raise ValueError("mevcut_aylik pozitif olmalı")

    kayit: dict[str, Any] = {}
    if donem is None:
        p = yukle()
        donem = max(p["emekli"]["donemler"])
    try:
        donemler = yukle(int(donem.split("-")[0]))["emekli"]["donemler"]
    except ValueError:
        donemler = {}  # veri dosyası olmayan (ör. gelecek) yıl: yalnızca senaryo hesabı yapılabilir
    if donem in donemler:
        kayit = donemler[donem]
    elif zam_orani_yuzde is None:
        raise ValueError(f"{donem} dönemi için kayıtlı oran yok; zam_orani_yuzde verin. Kayıtlı dönemler: {sorted(donemler)}")

    senaryo = zam_orani_yuzde is not None
    oran = d(zam_orani_yuzde) / 100 if senaryo else d(kayit["zam_orani"])
    zamli = yuvarla(aylik * (1 + oran))

    sonuc: dict[str, Any] = {
        "donem": donem,
        "mevcut_aylik": float(aylik),
        "zam_orani_yuzde": float(oran * 100),
        "zam_tutari": float(zamli - aylik),
        "zamli_aylik": float(zamli),
        "kaynak": "kullanıcı senaryosu" if senaryo else kayit["kaynak"],
    }
    en_dusuk = kayit.get("en_dusuk_aylik")
    if en_dusuk is not None and not senaryo:
        sonuc["en_dusuk_aylik"] = float(en_dusuk)
        if zamli < d(en_dusuk):
            sonuc["odenecek_tutar"] = float(en_dusuk)
            sonuc["not"] = (
                "Zamlı aylık en düşük emekli aylığının altında kaldığı için ödeme en düşük tutara "
                "tamamlanır (tüm SSK/Bağ-Kur aylıklarının toplamı dikkate alınır)."
            )
        else:
            sonuc["odenecek_tutar"] = float(zamli)
    return sonuc
