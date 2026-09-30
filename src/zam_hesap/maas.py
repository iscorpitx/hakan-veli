"""Ücretli çalışanlar için bordro hesapları (brütten nete, netten brüte, işveren maliyeti).

Varsayımlar:
- Çalışan yılbaşından itibaren her ay aynı brüt ücreti alır (kümülatif gelir vergisi matrahı buna göre oluşur).
- Engellilik indirimi, BES kesintisi, yan haklar, teşvikli istihdam gibi özel durumlar hesaba katılmaz.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from .parametreler import d, yukle

KURUS = Decimal("0.01")


def yuvarla(x: Decimal) -> Decimal:
    return x.quantize(KURUS, rounding=ROUND_HALF_UP)


def gelir_vergisi(matrah: Decimal, dilimler: list[dict[str, Any]]) -> Decimal:
    """Yıllık (kümülatif) matraha GVK 103 tarifesini uygular."""
    vergi = Decimal(0)
    alt = Decimal(0)
    for dilim in dilimler:
        ust = dilim["ust_sinir"]
        oran = d(dilim["oran"])
        if ust is None or matrah <= d(ust):
            return vergi + (matrah - alt) * oran
        vergi += (d(ust) - alt) * oran
        alt = d(ust)
    return vergi


def _aylik_vergi(kumulatif_once: Decimal, aylik_matrah: Decimal, dilimler) -> Decimal:
    return gelir_vergisi(kumulatif_once + aylik_matrah, dilimler) - gelir_vergisi(kumulatif_once, dilimler)


def asgari_brut(p: dict[str, Any], ay: int) -> Decimal:
    """Verilen ayda geçerli asgari brüt ücret (yıl içinde birden çok artış olabilir)."""
    gecerli = p["asgari_ucret"]["brut"]
    for degisim in p["asgari_ucret"].get("aylik_degisim", []):
        if degisim["ay"] <= ay:
            gecerli = degisim["brut"]
    return d(gecerli)


def _sgk_kesintileri(ucret: Decimal, ay: int, p: dict[str, Any]) -> tuple[Decimal, Decimal, Decimal]:
    """SGK işçi, işsizlik işçi payları ve gelir vergisi matrahı."""
    sgk = p["sgk"]
    prim_matrahi = min(ucret, asgari_brut(p, ay) * d(sgk["tavan_katsayisi"]))
    sgk_isci = yuvarla(prim_matrahi * d(sgk["isci_orani"]))
    issizlik = yuvarla(prim_matrahi * d(sgk["issizlik_isci_orani"]))
    return sgk_isci, issizlik, ucret - sgk_isci - issizlik


def _bordro_satiri(
    brut: Decimal, ay: int, p: dict[str, Any], onceki_kumulatif: Decimal | None = None
) -> dict[str, Decimal]:
    dilimler = p["gelir_vergisi"]["ucret_dilimleri"]
    damga_orani = d(p["damga_vergisi"]["oran"])
    asgari = asgari_brut(p, ay)

    sgk_isci, issizlik_isci, gv_matrahi = _sgk_kesintileri(brut, ay, p)
    # Asgari ücretin o aya kadarki kümülatif matrahı (istisna hesabı için)
    asgari_onceki = sum((_sgk_kesintileri(asgari_brut(p, a), a, p)[2] for a in range(1, ay)), Decimal(0))
    asgari_matrah = _sgk_kesintileri(asgari, ay, p)[2]

    if onceki_kumulatif is None:
        # Asgari ücretli yıl boyunca asgari ücret almıştır; diğerleri için aynı brüt varsayılır.
        onceki_kumulatif = asgari_onceki if brut == asgari else gv_matrahi * (ay - 1)
    hesaplanan_gv = yuvarla(_aylik_vergi(onceki_kumulatif, gv_matrahi, dilimler))
    # Asgari ücrete isabet eden gelir vergisi istisnası (GVK 23/18)
    gv_istisnasi = yuvarla(_aylik_vergi(asgari_onceki, asgari_matrah, dilimler))
    gv_istisnasi = min(gv_istisnasi, hesaplanan_gv)

    hesaplanan_damga = yuvarla(brut * damga_orani)
    damga_istisnasi = min(yuvarla(asgari * damga_orani), hesaplanan_damga)

    odenecek_gv = hesaplanan_gv - gv_istisnasi
    odenecek_damga = hesaplanan_damga - damga_istisnasi
    net = brut - sgk_isci - issizlik_isci - odenecek_gv - odenecek_damga

    return {
        "ay": ay,
        "brut": brut,
        "sgk_isci": sgk_isci,
        "issizlik_isci": issizlik_isci,
        "gelir_vergisi_matrahi": gv_matrahi,
        "kumulatif_matrah": onceki_kumulatif + gv_matrahi,
        "hesaplanan_gelir_vergisi": hesaplanan_gv,
        "gelir_vergisi_istisnasi": gv_istisnasi,
        "odenecek_gelir_vergisi": odenecek_gv,
        "hesaplanan_damga_vergisi": hesaplanan_damga,
        "damga_vergisi_istisnasi": damga_istisnasi,
        "odenecek_damga_vergisi": odenecek_damga,
        "net": net,
    }


def _disari(satir: dict[str, Decimal]) -> dict[str, Any]:
    return {k: (v if isinstance(v, int) else float(v)) for k, v in satir.items()}


def _ay_kontrol(ay: int) -> None:
    if not 1 <= ay <= 12:
        raise ValueError("ay 1 ile 12 arasında olmalı")


def _onceki(onceki_kumulatif_matrah: float | None) -> Decimal | None:
    if onceki_kumulatif_matrah is None:
        return None
    if onceki_kumulatif_matrah < 0:
        raise ValueError("onceki_kumulatif_matrah negatif olamaz")
    return d(onceki_kumulatif_matrah)


def brutten_nete(
    brut: float, ay: int = 1, yil: int | None = None, onceki_kumulatif_matrah: float | None = None
) -> dict[str, Any]:
    """Belirli bir ayın bordrosunu hesaplar.

    onceki_kumulatif_matrah: o aydan ÖNCEKİ aylarda birikmiş gelir vergisi matrahı. Verilmezse
    yılbaşından beri aynı brüt ücretin alındığı varsayılır. Bordrodaki "kümülatif matrah" bu ay dahil
    olduğundan, bordrodan alınan değerden bu ayın gelir vergisi matrahı çıkarılmalıdır.
    """
    _ay_kontrol(ay)
    p = yukle(yil)
    brut_d = d(brut)
    asgari = asgari_brut(p, ay)
    if brut_d < asgari:
        raise ValueError(f"Brüt ücret, {p['yil']}/{ay} asgari brüt ücretinden ({asgari} TL) düşük olamaz")
    return {"yil": p["yil"], **_disari(_bordro_satiri(brut_d, ay, p, _onceki(onceki_kumulatif_matrah)))}


def yillik_bordro(brut: float, yil: int | None = None) -> dict[str, Any]:
    """12 aylık bordro tablosu ve yıllık toplamlar."""
    p = yukle(yil)
    aylar = [_bordro_satiri(d(brut), ay, p) for ay in range(1, 13)]
    toplam_alanlar = ["brut", "sgk_isci", "issizlik_isci", "odenecek_gelir_vergisi", "odenecek_damga_vergisi", "net"]
    toplam = {k: float(sum(a[k] for a in aylar)) for k in toplam_alanlar}
    return {"yil": p["yil"], "aylar": [_disari(a) for a in aylar], "yillik_toplam": toplam}


def netten_brute(
    net: float, ay: int = 1, yil: int | None = None, onceki_kumulatif_matrah: float | None = None
) -> dict[str, Any]:
    """İstenen aylık net ücrete karşılık gelen brüt ücreti bulur (ikili arama)."""
    _ay_kontrol(ay)
    p = yukle(yil)
    hedef = d(net)
    onceki = _onceki(onceki_kumulatif_matrah)
    alt = asgari_brut(p, ay)
    if _bordro_satiri(alt, ay, p, onceki)["net"] > hedef:
        raise ValueError("İstenen net ücret, asgari ücretin netinden düşük")
    ust = hedef * 3
    while ust - alt > KURUS:
        orta = yuvarla((alt + ust) / 2)
        if orta in (alt, ust):
            break
        if _bordro_satiri(orta, ay, p, onceki)["net"] < hedef:
            alt = orta
        else:
            ust = orta
    # Net'i hedefe en yakın getiren kuruşu seç.
    aday = min((alt, ust), key=lambda b: abs(_bordro_satiri(b, ay, p, onceki)["net"] - hedef))
    return {"yil": p["yil"], "istenen_net": float(hedef), **_disari(_bordro_satiri(aday, ay, p, onceki))}


def isveren_maliyeti(brut: float, tesvik: str = "yok", yil: int | None = None) -> dict[str, Any]:
    """Brüt ücretin işverene aylık maliyeti.

    tesvik: "yok" (teşviksiz), "genel" (imalat dışı, 2 puan), "imalat" (5 puan).
    """
    p = yukle(yil)
    sgk = p["sgk"]
    if tesvik not in sgk["tesvik_puani"]:
        raise ValueError(f"tesvik şu değerlerden biri olmalı: {list(sgk['tesvik_puani'])}")
    brut_d = d(brut)
    prim_matrahi = min(brut_d, d(p["asgari_ucret"]["brut"]) * d(sgk["tavan_katsayisi"]))
    isveren_orani = d(sgk["isveren_orani"]) - d(sgk["tesvik_puani"][tesvik])
    sgk_isveren = yuvarla(prim_matrahi * isveren_orani)
    issizlik_isveren = yuvarla(prim_matrahi * d(sgk["issizlik_isveren_orani"]))
    return {
        "yil": p["yil"],
        "brut": float(brut_d),
        "tesvik": tesvik,
        "sgk_isveren_orani": float(isveren_orani),
        "sgk_isveren": float(sgk_isveren),
        "issizlik_isveren": float(issizlik_isveren),
        "toplam_maliyet": float(brut_d + sgk_isveren + issizlik_isveren),
    }


def asgari_ucret(yil: int | None = None) -> dict[str, Any]:
    """Asgari ücretin brüt, net ve işveren maliyeti özeti."""
    p = yukle(yil)
    brut = p["asgari_ucret"]["brut"]
    son_ay = max([x["ay"] for x in p["asgari_ucret"].get("aylik_degisim", [])] or [1])
    bordro = brutten_nete(brut, son_ay, p["yil"])
    return {
        "yil": p["yil"],
        "brut": float(brut),
        "net": bordro["net"],
        "sgk_isci": bordro["sgk_isci"],
        "issizlik_isci": bordro["issizlik_isci"],
        "isveren_maliyeti": {t: isveren_maliyeti(brut, t, p["yil"])["toplam_maliyet"] for t in p["sgk"]["tesvik_puani"]},
        "kaynak": p["asgari_ucret"]["kaynak"],
    }


def _yuzde(oran: Decimal) -> str:
    return f"{float(oran) * 100:g}".replace(".", ",")


def asgari_ucret_senaryosu(
    zam_oranlari_yuzde: list[float] | None = None,
    yeni_netler: list[float] | None = None,
    yil: int | None = None,
) -> dict[str, Any]:
    """Asgari ücrete gelecek zam için senaryolar (ör. %20, %25, %30...).

    Zam oranı ya da açıklanan yeni net tutar verilebilir. Hesap, verilen yılın (varsayılan: en güncel)
    SGK ve vergi kurallarıyla yapılır; asgari ücretin vergi istisnasının süreceği varsayılır.
    """
    if not zam_oranlari_yuzde and not yeni_netler:
        raise ValueError("zam_oranlari_yuzde veya yeni_netler verilmeli")
    p = yukle(yil)
    sgk = p["sgk"]
    mevcut_brut = d(p["asgari_ucret"]["brut"])
    kesinti_orani = d(sgk["isci_orani"]) + d(sgk["issizlik_isci_orani"])
    isveren_orani = d(sgk["isveren_orani"]) + d(sgk["issizlik_isveren_orani"])
    mevcut_net = mevcut_brut - yuvarla(mevcut_brut * d(sgk["isci_orani"])) - yuvarla(mevcut_brut * d(sgk["issizlik_isci_orani"]))

    def satir(brut: Decimal, oran: Decimal) -> dict[str, Any]:
        sgk_isci = yuvarla(brut * d(sgk["isci_orani"]))
        issizlik = yuvarla(brut * d(sgk["issizlik_isci_orani"]))
        net = brut - sgk_isci - issizlik
        maliyet = brut + yuvarla(brut * d(sgk["isveren_orani"])) + yuvarla(brut * d(sgk["issizlik_isveren_orani"]))
        return {
            "zam_orani_yuzde": float(yuvarla(oran * 100)),
            "brut": float(brut),
            "net": float(net),
            "net_artis": float(net - mevcut_net),
            "isveren_maliyeti_tesviksiz": float(maliyet),
        }

    senaryolar = [satir(yuvarla(mevcut_brut * (1 + d(o) / 100)), d(o) / 100) for o in zam_oranlari_yuzde or []]
    for net in yeni_netler or []:
        brut = yuvarla(d(net) / (1 - kesinti_orani))
        senaryolar.append(satir(brut, brut / mevcut_brut - 1))

    return {
        "baz_yil": p["yil"],
        "mevcut": {"brut": float(mevcut_brut), "net": float(mevcut_net)},
        "senaryolar": senaryolar,
        "not": (
            f"Tahmindir. {p['yil']} yılı SGK oranlarıyla (işçi %{_yuzde(kesinti_orani)}, işveren "
            f"%{_yuzde(isveren_orani)}) ve asgari ücretin vergiden istisna kalacağı varsayımıyla hesaplandı."
        ),
    }
