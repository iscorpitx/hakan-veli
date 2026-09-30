"""Yıllık parametre dosyalarını (veriler/<yil>.yaml) yükler."""

from __future__ import annotations

from decimal import Decimal
from functools import lru_cache
from importlib import resources
from typing import Any

import yaml


def desteklenen_yillar() -> list[int]:
    dosyalar = resources.files("zam_hesap").joinpath("veriler").iterdir()
    return sorted(int(d.name.removesuffix(".yaml")) for d in dosyalar if d.name.endswith(".yaml"))


@lru_cache
def yukle(yil: int | None = None) -> dict[str, Any]:
    """Verilen yılın parametrelerini döndürür. Yıl verilmezse en güncel yıl kullanılır."""
    yillar = desteklenen_yillar()
    if yil is None:
        yil = yillar[-1]
    if yil not in yillar:
        raise ValueError(f"{yil} yılı için veri yok. Desteklenen yıllar: {yillar}")
    metin = resources.files("zam_hesap").joinpath("veriler", f"{yil}.yaml").read_text(encoding="utf-8")
    return yaml.safe_load(metin)


def d(deger: Any) -> Decimal:
    """float/int/str değeri kuruş hassasiyetinde hesap için Decimal'e çevirir."""
    return Decimal(str(deger))
