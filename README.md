# zam-hesap-mcp

**Claude'a "emekli maaşım Temmuz'da ne kadar olur?" diye sorduğunuzda tahmin değil, kuruşu kuruşuna hesap.**

Türkiye'de maaş, asgari ücret, emekli ve memur zammı, kıdem-ihbar tazminatı, yıllık izin ve fazla mesai hesaplarını yapan bir [MCP](https://modelcontextprotocol.io) sunucusu. Claude Desktop, Claude Code, Cursor ve MCP destekleyen diğer yapay zekâ asistanlarıyla çalışır.

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
| `asgari_ucret_senaryosu` | "%25 zam gelirse?" gibi senaryolar: birden çok oran veya açıklanan net tutar için brüt, net, işveren maliyeti |
| `emekli_zammi` | SSK / Bağ-Kur emeklisinin zamlı aylığı; en düşük aylık desteği alanlar için asıl aylık üzerinden hesap |
| `emekli_zam_senaryosu` | Gelecek emekli zammı için karşılaştırma: "%10, %15, %20 gelirse?" |
| `memur_zammi` | Memur maaşı ve memur emeklisi (4/c) zammı |
| `memur_zam_senaryosu` | Gelecek memur zammı: oranlarla ya da toplu sözleşme + enflasyon senaryolarıyla (enflasyon farkı dahil) |
| `tis_zammi` | Belediye, kamu veya özel sektör işçisinin toplu sözleşme zammı: yeni brüt ve net |
| `kamu_isci_protokolu` | Kamu işçisi çerçeve protokolü zam oranları |
| `kumulatif_enflasyon` | Aylık enflasyonlardan birikimli oran (zam tahmini için) |
| `kidem_tazminati` | Kıdem tazminatı (tavan, küsurat, damga vergisi); ileri tarihli çıkış için tahmini tavan |
| `ihbar_tazminati` | İhbar süresi ve tazminatı (gelir ve damga vergisi dahil) |
| `hizmet_suresi` | İki tarih arası çalışma süresi |
| `yillik_izin` | Yıllık izin gün sayısı (yaş ve yer altı kuralları dahil) |
| `izin_ucreti` | Kullanılmayan izin ücreti, brüt ve net |
| `fazla_mesai` | Fazla mesai ücreti (%50 / %25 zamlı) |
| `tatil_mesaisi` | Bayram ve genel tatilde çalışma ek ödemesi |
| `guncel_parametreler` | Kullanılan tüm oranlar ve kaynakları |

## Örnek sorular

- "Emekli aylığım 21.000 TL, Temmuz zammından sonra ne kadar olur?"
- "En düşük emekli aylığını alıyorum (20.000 TL), asıl aylığım 15.000 TL. Temmuz'da ne alacağım?"
- "Brüt 50.000 TL maaşın Ocak ve Aralık'taki neti ne?"
- "Eline net 60.000 TL geçmesi için brüt kaç olmalı?"
- "Asgari ücretli bir çalışanın işverene maliyeti ne?"
- "Asgari ücrete %25, %30 ya da %35 zam gelirse net ne olur?"
- "Enflasyon önümüzdeki 6 ay ayda %2 olursa emekli zammı yüzde kaç olur?"
- "Memurum, net maaşım 62.000 TL, Temmuz zammıyla ne olur?"
- "Ocak'ta enflasyon %8, %10 ya da %12 çıkarsa memur zammı ne olur? Toplu sözleşme %5, önceki dönem %7."
- "Emekli aylığım 25.000 TL, Ocak'ta %10, %13, %15 zam gelirse ne alırım?"
- "Belediyede işçiyim, brüt 40.000 TL, TİS'te %10 ve %6 zam var, yeni netim ne?"
- "2019 Mart'ta girdim, bu ay çıkarıldım, giydirilmiş brütüm 55.000 TL. Kıdem ve ihbar ne kadar?"
- "8 yıllık çalışanım, kaç gün yıllık iznim var?"

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
| Memur / 4/c emekli zammı Ocak 2026 | %18,60 + 1.000 TL taban aylık (en düşük 4/c aylığı 27.772 TL) |
| Memur / 4/c emekli zammı Temmuz 2026 | %13,52 (%7 toplu sözleşme + %6,09 enflasyon farkı) |
| Kıdem tazminatı tavanı | Ocak–Haziran 64.948,77 TL · Temmuz–Aralık 73.729,87 TL |
| Kamu işçisi çerçeve protokolü | 2026 ilk yarı %10 · ikinci yarı %6 (+ enflasyon farkı) |

Tüm değerler [`src/zam_hesap/veriler/2026.yaml`](src/zam_hesap/veriler/2026.yaml) dosyasında, kaynaklarıyla birlikte durur.

## Varsayımlar ve sınırlar

- Çalışanın yılbaşından beri her ay aynı brüt ücreti aldığı varsayılır.
- Engellilik indirimi, BES, yan haklar, teşvikli istihdam gibi özel durumlar henüz yoktur.
- Memur zammı, net maaşa toplam oranın uygulanmasıyla yaklaşık hesaplanır. Kişiye özel kalemler (aile/çocuk yardımı, vergi dilimi, Ocak 2026'daki 1.000 TL taban aylık artışı) nedeniyle gerçek tutar birkaç yüz TL farklı olabilir. Unvana göre tam memur bordrosu henüz yoktur.
- Kıdem tazminatında küsurat ay/12 ve gün/365 olarak orantılanır. Tazminat hakkının doğup doğmadığı (istifa, haklı fesih vb.) araç tarafından değerlendirilmez.
- İhbar tazminatı ve izin ücretinde gelir vergisi, verilen kümülatif matraha göre hesaplanır (varsayılan 0, yani %15).

## Yol haritası

- [x] Memur ve memur emeklisi zammı
- [x] Kıdem ve ihbar tazminatı
- [x] Belediye / kamu işçisi TİS zammı
- [x] Yıllık izin, izin ücreti, fazla mesai, tatil mesaisi
- [ ] Unvana göre tam memur bordrosu (katsayılar, gösterge, ek gösterge, tazminatlar)
- [ ] Engellilik indirimi, BES, SGDP (emekli çalışan)
- [ ] 2027 parametreleri (Ocak 2027'de)
- [ ] PyPI yayını (`uvx zam-hesap-mcp`)

## Geliştirme

```bash
uv venv && uv pip install -e ".[test]"
uv run --no-sync pytest -q
```

Yeni bir zam döneminde yalnızca `veriler/<yıl>.yaml` güncellenir ve testlere o dönemin resmi örnekleri eklenir.

Hata bulursanız lütfen örnek bordro/hesapla birlikte [issue açın](https://github.com/iscorpitx/hakan-veli/issues).

## Yayınlama (PyPI)

Paket PyPI'ye yüklendiğinde herkes `uvx zam-hesap-mcp` ile kurabilir. Bir kerelik ayar:

1. [pypi.org](https://pypi.org) hesabı açın.
2. *Account → Publishing → Add a new pending publisher* bölümüne şunları girin: proje adı `zam-hesap-mcp`, sahip `iscorpitx`, depo `hakan-veli`, workflow `publish.yml`, environment `pypi`.
3. GitHub'da *Releases → Draft a new release* ile `v0.2.0` etiketli bir sürüm yayımlayın. Testler geçerse paket otomatik yüklenir.

## Lisans

MIT
