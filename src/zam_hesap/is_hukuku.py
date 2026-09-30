"""4857 sayılı İş Kanunu hesapları: kıdem, ihbar, yıllık izin, fazla mesai, TİS zammı."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from . import maas
from .maas import yuvarla
from .parametreler import d, yukle


def _tarih(t: str | date) -> date:
    return t if isinstance(t, date) else date.fromisoformat(t)


def _ay_ekle(t: date, ay: int) -> date:
    yil, ay_ = divmod(t.month - 1 + ay, 12)
    yeni_yil, yeni_ay = t.year + yil, ay_ + 1
    # Ayın son gününü aşmamak için
    for gun in range(t.day, 27, -1):
        try:
            return date(yeni_yil, yeni_ay, gun)
        except ValueError:
            continue
    return date(yeni_yil, yeni_ay, min(t.day, 28))


def hizmet_suresi(giris: str | date, cikis: str | date) -> dict[str, int]:
    """Giriş ve çıkış tarihleri arasındaki süre (yıl, ay, gün ve toplam gün)."""
    g, c = _tarih(giris), _tarih(cikis)
    if c < g:
        raise ValueError("çıkış tarihi giriş tarihinden önce olamaz")
    toplam_ay = (c.year - g.year) * 12 + (c.month - g.month)
    if _ay_ekle(g, toplam_ay) > c:
        toplam_ay -= 1
    gun = (c - _ay_ekle(g, toplam_ay)).days
    return {"yil": toplam_ay // 12, "ay": toplam_ay % 12, "gun": gun, "toplam_gun": (c - g).days, "toplam_ay": toplam_ay}


def _donem(t: date) -> str:
    return f"{t.year}-{'01' if t.month <= 6 else '07'}"


def _kesintiler(brut: Decimal, onceki_kumulatif_matrah: Decimal, p: dict[str, Any], gelir_vergili: bool) -> dict[str, Decimal]:
    damga = yuvarla(brut * d(p["damga_vergisi"]["oran"]))
    gv = Decimal(0)
    if gelir_vergili:
        dilimler = p["gelir_vergisi"]["ucret_dilimleri"]
        gv = yuvarla(
            maas.gelir_vergisi(onceki_kumulatif_matrah + brut, dilimler)
            - maas.gelir_vergisi(onceki_kumulatif_matrah, dilimler)
        )
    return {"gelir_vergisi": gv, "damga_vergisi": damga, "net": brut - gv - damga}


def kidem_tazminati(giydirilmis_brut: float, giris: str, cikis: str, tavan: float | None = None) -> dict[str, Any]:
    """Kıdem tazminatı. giydirilmis_brut: son brüt ücret + düzenli yan ödemeler (yemek, yol, ikramiye payı vb.).

    En az 1 yıl çalışma gerekir. Her tam yıl için 30 günlük ücret, artan süre orantılı eklenir.
    Tavan çıkış tarihindeki döneme göre uygulanır. Kıdem tazminatından yalnızca damga vergisi kesilir.
    tavan: kayıtlı olmayan (ileri tarihli) dönemler veya senaryo için tavan tutarı.
    """
    c = _tarih(cikis)
    sure = hizmet_suresi(giris, c)
    donem = _donem(c)
    tahmini = tavan is not None
    try:
        p = yukle(c.year)
    except ValueError:
        if not tahmini:
            raise ValueError(f"{c.year} yılı için veri yok; tahmini hesap için tavan verin.") from None
        p = yukle()
    tavanlar = p["kidem_tazminati"]["tavan"]
    if not tahmini and donem not in tavanlar:
        raise ValueError(f"{donem} dönemi için kıdem tavanı kayıtlı değil; tahmini hesap için tavan verin. Kayıtlı: {sorted(tavanlar)}")
    tavan = d(tavan) if tahmini else d(tavanlar[donem])
    ucret = d(giydirilmis_brut)
    esas = min(ucret, tavan)

    sonuc: dict[str, Any] = {"hizmet_suresi": sure, "giydirilmis_brut": float(ucret), "tavan": float(tavan), "esas_ucret": float(esas)}
    if tahmini:
        sonuc["tavan_kaynagi"] = "kullanıcı tahmini"
    if sure["yil"] < 1:
        return {**sonuc, "brut_tazminat": 0.0, "damga_vergisi": 0.0, "net_tazminat": 0.0, "not": "Kıdem tazminatı için en az 1 yıl çalışma gerekir."}

    brut = yuvarla(esas * sure["yil"] + esas * sure["ay"] / 12 + esas * sure["gun"] / 365)
    k = _kesintiler(brut, Decimal(0), p, gelir_vergili=False)
    sonuc.update({"brut_tazminat": float(brut), "damga_vergisi": float(k["damga_vergisi"]), "net_tazminat": float(k["net"])})
    if ucret > tavan:
        sonuc["not"] = "Giydirilmiş ücret tavanı aştığı için hesap tavan üzerinden yapıldı."
    return sonuc


def ihbar_suresi_gun(sure: dict[str, int]) -> int:
    ay = sure["toplam_ay"]
    if ay < 6:
        return 14
    if ay < 18:
        return 28
    if ay < 36:
        return 42
    return 56


def ihbar_tazminati(giydirilmis_brut: float, giris: str, cikis: str, onceki_kumulatif_matrah: float = 0) -> dict[str, Any]:
    """İhbar tazminatı: bildirim süresine uyulmadan işten çıkarmada ödenir. Tavan yoktur.

    onceki_kumulatif_matrah: çıkış yılındaki kümülatif gelir vergisi matrahı (vergi dilimini belirler).
    """
    c = _tarih(cikis)
    sure = hizmet_suresi(giris, c)
    p = yukle(c.year)
    gun = ihbar_suresi_gun(sure)
    brut = yuvarla(d(giydirilmis_brut) / 30 * gun)
    k = _kesintiler(brut, d(onceki_kumulatif_matrah), p, gelir_vergili=True)
    return {
        "hizmet_suresi": sure,
        "ihbar_suresi_gun": gun,
        "ihbar_suresi_hafta": gun // 7,
        "brut_tazminat": float(brut),
        "gelir_vergisi": float(k["gelir_vergisi"]),
        "damga_vergisi": float(k["damga_vergisi"]),
        "net_tazminat": float(k["net"]),
    }


def yillik_izin(hizmet_yili: int, yas: int | None = None, yeralti: bool = False) -> dict[str, Any]:
    """Yıllık ücretli izin süresi (İş Kanunu md. 53)."""
    if hizmet_yili < 1:
        return {"izin_gun": 0, "not": "Yıllık izin hakkı için en az 1 yıl çalışma gerekir."}
    gun = 14 if hizmet_yili <= 5 else 20 if hizmet_yili < 15 else 26
    notlar = []
    if yas is not None and (yas <= 18 or yas >= 50) and gun < 20:
        gun = 20
        notlar.append("18 yaş ve altı ile 50 yaş ve üstü çalışanlara en az 20 gün verilir.")
    if yeralti:
        gun += 4
        notlar.append("Yer altı işlerinde süre 4 gün artırılır.")
    sonuc: dict[str, Any] = {"hizmet_yili": hizmet_yili, "izin_gun": gun}
    if notlar:
        sonuc["not"] = " ".join(notlar)
    return sonuc


def izin_ucreti(brut: float, gun: int, yil: int | None = None, onceki_kumulatif_matrah: float = 0) -> dict[str, Any]:
    """Kullanılmayan yıllık izin ücreti (işten ayrılırken): günlük brüt x gün. SGK primine tabidir."""
    p = yukle(yil)
    brut_tutar = yuvarla(d(brut) / 30 * gun)
    sgk = yuvarla(brut_tutar * d(p["sgk"]["isci_orani"]))
    issizlik = yuvarla(brut_tutar * d(p["sgk"]["issizlik_isci_orani"]))
    k = _kesintiler(brut_tutar - sgk - issizlik, d(onceki_kumulatif_matrah), p, gelir_vergili=True)
    damga = yuvarla(brut_tutar * d(p["damga_vergisi"]["oran"]))
    net = brut_tutar - sgk - issizlik - k["gelir_vergisi"] - damga
    return {
        "gun": gun,
        "brut": float(brut_tutar),
        "sgk_isci": float(sgk),
        "issizlik_isci": float(issizlik),
        "gelir_vergisi": float(k["gelir_vergisi"]),
        "damga_vergisi": float(damga),
        "net": float(net),
    }


FAZLA_MESAI_CARPANLARI = {
    "fazla_calisma": Decimal("1.5"),  # haftalık 45 saati aşan çalışma
    "fazla_surelerle": Decimal("1.25"),  # sözleşmede 45 saatin altı belirlenmişse, 45 saate kadar olan kısım
}


def fazla_mesai(brut: float, saat: float, tur: str = "fazla_calisma") -> dict[str, Any]:
    """Fazla mesai brüt ücreti. Saatlik ücret = aylık brüt / 225 (İş Kanunu md. 41)."""
    if tur not in FAZLA_MESAI_CARPANLARI:
        raise ValueError(f"tur şunlardan biri olmalı: {list(FAZLA_MESAI_CARPANLARI)}")
    saatlik = d(brut) / 225
    carpan = FAZLA_MESAI_CARPANLARI[tur]
    return {
        "saatlik_brut": float(yuvarla(saatlik)),
        "carpan": float(carpan),
        "saat": saat,
        "fazla_mesai_brut": float(yuvarla(saatlik * carpan * d(saat))),
        "not": "Tutar brüttür; ay içindeki diğer ücretlerle birlikte bordroda vergilendirilir.",
    }


def tatil_mesaisi(brut: float, gun: float) -> dict[str, Any]:
    """Ulusal bayram / genel tatil gününde çalışma: çalışılan her gün için ayrıca 1 günlük ücret (İş Kanunu md. 47)."""
    gunluk = d(brut) / 30
    return {
        "gunluk_brut": float(yuvarla(gunluk)),
        "gun": gun,
        "ek_odeme_brut": float(yuvarla(gunluk * d(gun))),
        "not": "Aylık ücrete ek olarak ödenir; brüt tutardır.",
    }


def tis_zammi(
    mevcut_brut: float,
    zam_oranlari_yuzde: list[float],
    seyyanen_brut: float = 0,
    ay: int = 1,
    yil: int | None = None,
) -> dict[str, Any]:
    """Toplu iş sözleşmesi zammı (belediye/kamu/özel sektör işçisi).

    Önce seyyanen (sabit) tutar eklenir, sonra oranlar sırasıyla bileşik uygulanır.
    Sonuçta eski ve yeni brüt ücretin net karşılıkları da verilir.
    """
    eski = d(mevcut_brut)
    yeni = eski + d(seyyanen_brut)
    for oran in zam_oranlari_yuzde:
        yeni = yeni * (1 + d(oran) / 100)
    yeni = yuvarla(yeni)
    eski_net = maas.brutten_nete(float(eski), ay, yil)["net"]
    yeni_net = maas.brutten_nete(float(yeni), ay, yil)["net"]
    return {
        "mevcut_brut": float(eski),
        "zam_oranlari_yuzde": zam_oranlari_yuzde,
        "seyyanen_brut": seyyanen_brut,
        "yeni_brut": float(yeni),
        "toplam_artis_yuzde": float(yuvarla((yeni / eski - 1) * 100)),
        "mevcut_net": eski_net,
        "yeni_net": yeni_net,
        "net_artis": round(yeni_net - eski_net, 2),
        "hesap_ayi": ay,
    }


def kamu_isci_protokolu(yil: int | None = None) -> dict[str, Any]:
    """Kamu işçileri çerçeve protokolündeki dönemsel zam oranları."""
    p = yukle(yil)
    return {"yil": p["yil"], **p["kamu_isci"]}
