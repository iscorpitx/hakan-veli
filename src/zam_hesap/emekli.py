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


def _onceki_donem(donem: str) -> str:
    yil, ay = donem.split("-")
    return f"{yil}-01" if ay == "07" else f"{int(yil) - 1}-07"


def _donemler(yil: int) -> dict[str, Any]:
    try:
        return yukle(yil).get("emekli", {}).get("donemler", {})
    except ValueError:
        return {}  # veri dosyası olmayan (ör. gelecek) yıl


def emekli_zammi(
    mevcut_aylik: float,
    donem: str | None = None,
    zam_orani_yuzde: float | None = None,
    asil_aylik: float | None = None,
) -> dict[str, Any]:
    """Mevcut aylığa dönemin zammını uygular.

    mevcut_aylik: şu an eline geçen aylık.
    donem: "YYYY-01" veya "YYYY-07". Verilmezse en son kayıtlı dönem kullanılır.
    zam_orani_yuzde: verilirse kayıtlı oran yerine bu oran kullanılır (tahmin/senaryo için).
    asil_aylik: en düşük aylık desteği alanlar için desteksiz (bağlanan) aylık. Zam bu tutara
        uygulanır, sonra yeni en düşük aylığa tamamlanır. e-Devlet'te "aylık tutarı" olarak görülür.
    """
    aylik = d(mevcut_aylik)
    if aylik <= 0:
        raise ValueError("mevcut_aylik pozitif olmalı")
    asil = d(asil_aylik) if asil_aylik is not None else None
    if asil is not None and not 0 < asil <= aylik:
        raise ValueError("asil_aylik pozitif olmalı ve mevcut_aylik'tan büyük olmamalı")

    if donem is None:
        donem = max(yukle()["emekli"]["donemler"])
    donemler = _donemler(int(donem.split("-")[0]))
    kayit: dict[str, Any] = donemler.get(donem, {})
    senaryo = zam_orani_yuzde is not None
    if not kayit and not senaryo:
        raise ValueError(f"{donem} dönemi için kayıtlı oran yok; zam_orani_yuzde verin. Kayıtlı dönemler: {sorted(donemler)}")

    oran = d(zam_orani_yuzde) / 100 if senaryo else d(kayit["zam_orani"])
    esas = asil if asil is not None else aylik
    zamli = yuvarla(esas * (1 + oran))

    sonuc: dict[str, Any] = {
        "donem": donem,
        "mevcut_aylik": float(aylik),
        "zam_orani_yuzde": float(oran * 100),
    }
    if asil is not None:
        sonuc["asil_aylik"] = float(asil)
    sonuc.update({
        "zam_tutari": float(zamli - esas),
        "zamli_aylik": float(zamli),
        "kaynak": "kullanıcı senaryosu" if senaryo else kayit["kaynak"],
    })

    en_dusuk = kayit.get("en_dusuk_aylik")
    if en_dusuk is None or senaryo:
        return sonuc

    odenecek = max(zamli, d(en_dusuk))
    sonuc["en_dusuk_aylik"] = float(en_dusuk)
    sonuc["odenecek_tutar"] = float(odenecek)
    sonuc["gercek_artis"] = float(odenecek - aylik)
    notlar = []
    if zamli < d(en_dusuk):
        notlar.append(
            "Zamlı aylık en düşük emekli aylığının altında kaldığı için ödeme en düşük tutara "
            "tamamlanır (tüm SSK/Bağ-Kur aylıklarının toplamı dikkate alınır)."
        )
    onceki_en_dusuk = _donemler(int(_onceki_donem(donem).split("-")[0])).get(_onceki_donem(donem), {}).get("en_dusuk_aylik")
    if asil is None and onceki_en_dusuk is not None and aylik == d(onceki_en_dusuk):
        notlar.append(
            f"Mevcut aylık önceki dönemin en düşük aylığına ({onceki_en_dusuk:.0f} TL) eşit; en düşük aylık "
            "desteği alıyor olabilirsiniz. Öyleyse zam desteksiz asıl aylığa uygulanır: asil_aylik girin."
        )
    if notlar:
        sonuc["not"] = " ".join(notlar)
    return sonuc


def emekli_zam_senaryosu(
    mevcut_aylik: float,
    zam_oranlari_yuzde: list[float],
    asil_aylik: float | None = None,
    en_dusuk_aylik: float | None = None,
) -> dict[str, Any]:
    """Gelecek emekli zammı için birden çok oranla karşılaştırma tablosu.

    en_dusuk_aylik: yeni en düşük aylık biliniyorsa. Verilmezse mevcut en düşük aylığın da aynı
    oranda artacağı varsayılır (Temmuz 2026'da böyle oldu: 20.000 x 1,1776 = 23.552).
    """
    if not zam_oranlari_yuzde:
        raise ValueError("en az bir zam oranı verilmeli")
    aylik = d(mevcut_aylik)
    esas = d(asil_aylik) if asil_aylik is not None else aylik
    if aylik <= 0 or esas <= 0 or esas > aylik:
        raise ValueError("aylık tutarları pozitif olmalı; asil_aylik mevcut_aylik'tan büyük olamaz")
    p = yukle()
    mevcut_en_dusuk = d(p["emekli"]["donemler"][max(p["emekli"]["donemler"])]["en_dusuk_aylik"])

    senaryolar = []
    for oran_yuzde in zam_oranlari_yuzde:
        oran = d(oran_yuzde) / 100
        zamli = yuvarla(esas * (1 + oran))
        yeni_en_dusuk = d(en_dusuk_aylik) if en_dusuk_aylik is not None else yuvarla(mevcut_en_dusuk * (1 + oran))
        odenecek = max(zamli, yeni_en_dusuk)
        senaryolar.append({
            "zam_orani_yuzde": float(oran_yuzde),
            "zamli_aylik": float(zamli),
            "en_dusuk_aylik": float(yeni_en_dusuk),
            "odenecek_tutar": float(odenecek),
            "gercek_artis": float(odenecek - aylik),
            "tamamlama_var": zamli < yeni_en_dusuk,
        })
    sonuc: dict[str, Any] = {"mevcut_aylik": float(aylik), "senaryolar": senaryolar}
    if asil_aylik is not None:
        sonuc["asil_aylik"] = float(esas)
    if en_dusuk_aylik is not None:
        sonuc["not"] = "Tahmindir. Yeni en düşük aylık kullanıcıdan alındı."
    else:
        tutar = f"{float(mevcut_en_dusuk):,.0f}".replace(",", ".")
        sonuc["not"] = (
            f"Tahmindir. Yeni en düşük aylığın mevcut {tutar} TL'nin aynı oranda artacağı varsayıldı; "
            "yasal düzenlemeyle farklı belirlenebilir."
        )
    return sonuc
