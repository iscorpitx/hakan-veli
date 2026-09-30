"""Unvana göre memur maaşı (657 sayılı DMK): kalem kalem brüt, kesintiler ve net.

Kurallar:
- Gösterge, ek gösterge, kıdem (yıl x 20, en çok 25 yıl) ve aile yardımı göstergeleri aylık katsayıyla,
  taban aylık taban aylık katsayısıyla, yan ödeme puanı yan ödeme katsayısıyla çarpılır.
- Özel hizmet tazminatı, ek ödeme ve kariyer tazminatı en yüksek devlet memuru aylığının (9500 gösterge) oranıdır.
- 5510 (2008 sonrası): %9 malullük-yaşlılık + %5 GSS; matrah = gösterge + ek gösterge + taban + kıdem + ÖHT.
- 5434 (2008 öncesi): %16 emekli keseneği; matrah = gösterge + ek gösterge + taban + kıdem + tazminat payı.
- Gelir vergisi matrahı = gösterge + ek gösterge + taban + kıdem + yan ödeme - prim/kesenek - sendika aidatı.
  Özel hizmet tazminatı, ek ödeme, ilave ödeme ve kariyer tazminatından yalnızca damga vergisi kesilir.
- Asgari ücret gelir ve damga vergisi istisnası işçilerdeki gibi uygulanır.
"""

from __future__ import annotations

from decimal import ROUND_FLOOR, Decimal
from typing import Any

from . import maas
from .maas import yuvarla
from .parametreler import d, yukle

EMEKLILIK = ("5510", "5434")
KARIYER = (None, "uzman", "basogretmen")


def _katsayilar(m: dict[str, Any], ay: int) -> dict[str, Decimal]:
    gecerli = None
    for donem in m["donemler"]:
        if donem["ay"] <= ay:
            gecerli = donem
    return {k: d(v) for k, v in gecerli.items() if k != "ay"}


def _kesenek_orani(unvan: dict[str, Any], ek_gosterge: int) -> Decimal:
    for kural in unvan["kesenek_tazminat_orani"]:
        if ek_gosterge >= kural["ek_gosterge_en_az"]:
            return d(kural["oran"])
    return Decimal(0)


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
    """Memurun aylık maaş bordrosunu kalem kalem hesaplar."""
    p = yukle(yil)
    if "memur_maasi" not in p:
        raise ValueError(f"{p['yil']} yılı için memur maaşı verisi yok")
    m = p["memur_maasi"]
    if unvan not in m["unvanlar"]:
        raise ValueError(f"unvan şunlardan biri olmalı: {list(m['unvanlar'])}")
    if emeklilik not in EMEKLILIK:
        raise ValueError("emeklilik '5510' (2008 sonrası giriş) veya '5434' (2008 öncesi) olmalı")
    if kariyer not in KARIYER:
        raise ValueError("kariyer boş, 'uzman' veya 'basogretmen' olmalı")
    if not 1 <= ay <= 12:
        raise ValueError("ay 1 ile 12 arasında olmalı")
    tablo = m["gosterge_tablosu"]
    if derece not in tablo or not 1 <= kademe <= len(tablo[derece]):
        raise ValueError(f"{derece}/{kademe} geçerli bir derece/kademe değil")
    if hizmet_yili < 0 or cocuk_72_ay_alti < 0 or cocuk_72_ay_ustu < 0 or sendika_aidati < 0:
        raise ValueError("negatif değer girilemez")

    u = m["unvanlar"][unvan]
    k = _katsayilar(m, ay)
    ak = k["aylik_katsayi"]
    tazminat_tabani = m["tazminat_tabani_gostergesi"] * ak
    ek_gosterge = u["ek_gosterge"][derece]
    kidem_yil = min(hizmet_yili, m["kidem_azami_yil"])

    kalem = {
        "gosterge_ayligi": yuvarla(tablo[derece][kademe - 1] * ak),
        "ek_gosterge_ayligi": yuvarla(ek_gosterge * ak),
        "taban_ayligi": yuvarla(m["taban_aylik_gostergesi"] * k["taban_aylik_katsayisi"]),
        "kidem_ayligi": yuvarla(kidem_yil * m["kidem_gostergesi_yil_basina"] * ak),
        "yan_odeme": yuvarla(u["yan_odeme_puani"] * k["yan_odeme_katsayisi"]),
        "ozel_hizmet_tazminati": yuvarla(tazminat_tabani * d(u["ozel_hizmet_tazminati"][derece])),
        "ek_odeme": yuvarla(tazminat_tabani * d(u["ek_odeme"])),
        "ilave_odeme": yuvarla(u["ilave_seyyanen_gostergesi"] * ak),
        "kariyer_tazminati": yuvarla(tazminat_tabani * d(u["kariyer_tazminati"][kariyer])) if kariyer else Decimal(0),
    }
    aile = m["aile_yardimi"]
    yardim = {
        "es_yardimi": yuvarla(aile["es_gostergesi"] * ak) if es_calismiyor else Decimal(0),
        "cocuk_yardimi": yuvarla(
            (cocuk_72_ay_alti * aile["cocuk_72_ay_alti_gostergesi"] + cocuk_72_ay_ustu * aile["cocuk_72_ay_ustu_gostergesi"]) * ak
        ),
    }
    brut = sum(kalem.values(), Decimal(0))
    toplam = brut + sum(yardim.values(), Decimal(0))

    temel = kalem["gosterge_ayligi"] + kalem["ek_gosterge_ayligi"] + kalem["taban_ayligi"] + kalem["kidem_ayligi"]
    kes = m["kesintiler"]
    if emeklilik == "5510":
        prim_matrahi = temel + kalem["ozel_hizmet_tazminati"]
        kesinti = {
            "malulluk_yaslilik": yuvarla(prim_matrahi * d(kes["sgk_5510"]["malulluk_yaslilik"])),
            "gss": yuvarla(prim_matrahi * d(kes["sgk_5510"]["gss"])),
        }
    else:
        prim_matrahi = temel + yuvarla(tazminat_tabani * _kesenek_orani(u, ek_gosterge))
        kesinti = {"emekli_kesenegi": yuvarla(prim_matrahi * d(kes["emekli_kesenegi_5434"]))}
    prim_toplami = sum(kesinti.values(), Decimal(0))

    gv_matrahi = max(Decimal(0), temel + kalem["yan_odeme"] - prim_toplami - d(sendika_aidati))
    onceki = d(onceki_kumulatif_matrah) if onceki_kumulatif_matrah is not None else gv_matrahi * (ay - 1)
    dilimler = p["gelir_vergisi"]["ucret_dilimleri"]
    hesaplanan_gv = yuvarla(maas._aylik_vergi(onceki, gv_matrahi, dilimler))
    asgari = maas.asgari_brut(p, ay)
    asgari_onceki = sum((maas._sgk_kesintileri(maas.asgari_brut(p, a), a, p)[2] for a in range(1, ay)), Decimal(0))
    asgari_matrah = maas._sgk_kesintileri(asgari, ay, p)[2]
    gv_istisnasi = min(yuvarla(maas._aylik_vergi(asgari_onceki, asgari_matrah, dilimler)), hesaplanan_gv)

    damga_orani = d(p["damga_vergisi"]["oran"])
    hesaplanan_damga = yuvarla(brut * damga_orani)  # aile yardımından damga vergisi kesilmez
    damga_istisnasi = min(yuvarla(asgari * damga_orani), hesaplanan_damga)

    # BES katkı payı prim matrahının %3'ü; KBS tam lira olarak keser.
    bes_kesintisi = (prim_matrahi * d(p["bes"]["oran"])).to_integral_value(ROUND_FLOOR) if bes else Decimal(0)

    gelir_vergisi = hesaplanan_gv - gv_istisnasi
    damga = hesaplanan_damga - damga_istisnasi
    net = toplam - prim_toplami - gelir_vergisi - damga - bes_kesintisi - d(sendika_aidati)

    f = lambda x: {a: float(b) for a, b in x.items()}  # noqa: E731
    return {
        "yil": p["yil"],
        "ay": ay,
        "unvan": u["ad"] + ({"uzman": " - Uzman", "basogretmen": " - Başöğretmen"}[kariyer] if kariyer else ""),
        "derece_kademe": f"{derece}/{kademe}",
        "emeklilik": emeklilik,
        "kazanclar": f(kalem),
        "yardimlar": f(yardim),
        "toplam_kazanc": float(toplam),
        "kesintiler": {
            **f(kesinti),
            "gelir_vergisi": float(gelir_vergisi),
            "damga_vergisi": float(damga),
            "bes": float(bes_kesintisi),
            "sendika_aidati": float(d(sendika_aidati)),
        },
        "gelir_vergisi_matrahi": float(gv_matrahi),
        "kumulatif_matrah": float(onceki + gv_matrahi),
        "hesaplanan_gelir_vergisi": float(hesaplanan_gv),
        "gelir_vergisi_istisnasi": float(gv_istisnasi),
        "damga_vergisi_istisnasi": float(damga_istisnasi),
        "net": float(net),
        "not": "Ek ders ücreti, fazla mesai, lojman, dil tazminatı gibi kişiye özel ödemeler dahil değildir.",
    }
