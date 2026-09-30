# zam-hesap-mcp

**Claude'a "emekli maaşım Temmuz'da ne kadar olur?" diye sorduğunuzda tahmin değil, kuruşu kuruşuna hesap.**

Türkiye'de maaş, asgari ücret ve emekli zammı hesaplarını yapan bir [MCP](https://modelcontextprotocol.io) sunucusu. Claude Desktop, Claude Code, Cursor ve MCP destekleyen diğer yapay zekâ asistanlarıyla çalışır.

> ⚠️ Sonuçlar bilgilendirme amaçlıdır, resmi bordro veya SGK hesabı yerine geçmez.

## Neden?

Yapay zekâ modelleri Türk vergi ve SGK hesaplarında sık hata yapar: vergi dilimleri kümülatif, asgari ücret istisnası her ay değişir, oranlar yılda bir-iki kez güncellenir. Bu sunucu hesabı modele bırakmaz; model araçları çağırır, rakamlar koddan gelir.

## Neler hesaplanıyor?

| Araç | Ne yapar |
|---|---|
| `brutten_nete` | Brüt ücretten net ücret (SGK, işsizlik, gelir ve damga vergisi, asgari ücret istisnası) |
| `netten_brute` | İstenen net ücret için gereken brüt ücret |
| `yillik_bordro` | 12 aylık bordro tablosu ve yıllık toplamlar |
| `isveren_maliyeti` | Brüt ücretin işverene maliyeti (teşviksiz / 2 puan / imalat 5 puan) |
| `asgari_ucret` | Asgari ücretin brüt, net ve işveren maliyeti |
| `emekli_zammi` | SSK / Bağ-Kur emeklisinin zamlı aylığı, en düşük aylık tamamlaması dahil |
| `kumulatif_enflasyon` | Aylık enflasyonlardan birikimli oran (zam tahmini için) |
| `guncel_parametreler` | Kullanılan tüm oranlar ve kaynakları |

## Örnek sorular

- "Emekli aylığım 21.000 TL, Temmuz zammından sonra ne kadar olur?"
- "Brüt 50.000 TL maaşın Ocak ve Aralık'taki neti ne?"
- "Eline net 60.000 TL geçmesi için brüt kaç olmalı?"
- "Asgari ücretli bir çalışanın işverene maliyeti ne?"
- "Enflasyon önümüzdeki 6 ay ayda %2 olursa emekli zammı yüzde kaç olur?"

## Kurulum

[uv](https://docs.astral.sh/uv/getting-started/installation/) kurulu olmalı.

### Claude Desktop

`claude_desktop_config.json` dosyasına ekleyin
(Windows: `%APPDATA%\Claude\claude_desktop_config.json`, macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "zam-hesap": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/iscorpitx/hakan-veli", "zam-hesap-mcp"]
    }
  }
}
```

Claude Desktop'ı yeniden başlatın.

### Claude Code

```bash
claude mcp add zam-hesap -- uvx --from git+https://github.com/iscorpitx/hakan-veli zam-hesap-mcp
```

## Desteklenen dönemler

| Veri | Değer (2026) |
|---|---|
| Asgari ücret (brüt / net) | 33.030,00 TL / 28.075,50 TL |
| SGK işçi / işsizlik işçi | %14 / %1 |
| SGK işveren / işsizlik işveren | %21,75 / %2 |
| SGK tavanı | Asgari brüt × 9 = 297.270,00 TL |
| Gelir vergisi (ücret) | 190 bin %15 · 400 bin %20 · 1,5 milyon %27 · 5,3 milyon %35 · üstü %40 |
| Damga vergisi | ‰7,59 |
| Emekli zammı Ocak 2026 | %12,19 (en düşük aylık 20.000 TL) |
| Emekli zammı Temmuz 2026 | %17,76 (en düşük aylık 23.552 TL) |

Tüm değerler [`src/zam_hesap/veriler/2026.yaml`](src/zam_hesap/veriler/2026.yaml) dosyasında, kaynaklarıyla birlikte durur.

## Varsayımlar ve sınırlar

- Çalışanın yılbaşından beri her ay aynı brüt ücreti aldığı varsayılır.
- Engellilik indirimi, BES, yan haklar, teşvikli istihdam gibi özel durumlar henüz yoktur.
- Emekli hesabı yalnızca SSK (4/a) ve Bağ-Kur (4/b) içindir; memur ve Emekli Sandığı (4/c) hesabı yol haritasındadır.

## Yol haritası

- [ ] Memur maaşı ve memur emeklisi (toplu sözleşme + enflasyon farkı)
- [ ] Kıdem ve ihbar tazminatı
- [ ] Belediye / kamu işçisi TİS zammı
- [ ] Yıllık izin ücreti, fazla mesai
- [ ] PyPI yayını (`uvx zam-hesap-mcp`)

## Geliştirme

```bash
uv venv && uv pip install -e ".[test]"
uv run --no-sync pytest -q
```

Yeni bir zam döneminde yalnızca `veriler/<yıl>.yaml` güncellenir ve testlere o dönemin resmi örnekleri eklenir.

Hata bulursanız lütfen örnek bordro/hesapla birlikte [issue açın](https://github.com/iscorpitx/hakan-veli/issues).

## Lisans

MIT
