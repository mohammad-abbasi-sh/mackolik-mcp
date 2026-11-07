# mackolik-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/mackolik-mcp

mackolik.com için resmi olmayan **salt okunur** MCP sunucusu — Türkiye'nin 1 numaralı canlı skor uygulaması (~38 milyon indirme): dünya genelinde futbol (ve basketbol) için canlı skorlar, sonuçlar, fikstürler, puan durumları ve maç detayları; Türkiye ligleri öncelikli.

> Mohammad Abbasi tarafından "Turkey MCP factory" (Sepehr tarzı hat) kapsamında geliştirildi. mackolik.com ile bağlantısı yoktur. Yalnızca Mackolik için geliştirildi — Sahadan asla (aynı sahip, aynı veri).

## Yapay zekâ ajanları için

MCP istemci yapılandırmanıza ekleyin (stdio):

```json
{
  "mcpServers": {
    "mackolik": {
      "command": "uvx",
      "args": ["mackolik-mcp"]
    }
  }
}
```

Veya yerel çalıştırın: `python -m mackolik_mcp.server` (`mcp<2`, `curl-cffi` gerekir).

## Araçlar

| Araç | Açıklama |
|------|----------|
| `mackolik_live_scores` | Şu an oynanan maçlar — `league` isteğe bağlı alt dize filtresi (örn. "Süper Lig", "Premier Lig"), `limit` 1..50; dakika, skor, ilk yarı, kırmızı kartlar, 1/X/2 oranları |
| `mackolik_results` | Bir tarihte biten maçlar (varsayılan bugün) — `date` YYYY-MM-DD veya DD/MM/YYYY, `league` filtresi, `limit` 1..50 |
| `mackolik_fixtures` | Bir tarihte oynanacak maçlar (varsayılan bugün) — results ile aynı parametreler |
| `mackolik_standings` | Lig puan durumu — `league`: Tur (Türkiye Süper Lig), Eng (Premier Lig), Esp (LaLiga), Ita (Serie A), Ger (Bundesliga); sıra, takım, oynanan, puan, averaj |
| `mackolik_match_detail` | Bir maçın tüm detayı — `match_id` (diğer araçlardan) + isteğe bağlı `date` (akış günlük olduğu için geçmiş maçın tarihi gerekir) |

Örnek çıktı (`mackolik_live_scores` / 2026-11-07):

```json
{"total_live": 34, "matches": [
  {"match_id": 4542744, "home_team": "Eyüpspor", "away_team": "Kocaelispor",
   "league": "Süper Lig", "country": "Türkiye", "date": "07/11/2026",
   "time": "13:30", "status": "live", "status_text": "17",
   "score": "0-0", "odds_1": "3.46", "odds_x": "2.97", "odds_2": "1.78",
   "url": "https://arsiv.mackolik.com/Futbol-Mac/4542744/eyupspor-kocaelispor"}, …]}
```

Örnek çıktı (`mackolik_standings` / Tur):

```json
{"league": "Tur", "league_name": "Türkiye", "count": 9, "standings": [
  {"rank": 1, "team": "Galatasaray", "played": 10, "points": 25,
   "goal_difference": 11}, …]}
```

## Nasıl çalışıyor?

mackolik.com, arsiv.mackolik.com'a yönlendirir (Akamai ön yüzü, bot duvarı yok). Canlı veriler sitenin kendi JSON akışından gelir: `vd.mackolik.com/livedata` — sitenin JavaScript'i `?group=0` (bugünün tamamı, 2026-11-07'de 836 maç) veya `?date=DD/MM/YYYY` (07/11/2026 için 1.370 maç) ile çağırır; giriş ve API anahtarı gerekmez. Maç satırları, sitenin kendi `livescore-go.js` dosyasına göre çözümlenen dizilerdir: id, takımlar, durum kodu, durum metni, skor, ilk yarı/kırmızı kart detayı, başlama saati, 1/X/2 iddaa oranları (yalnızca bilgi amaçlı), tarih ve lig grubu (ülke, lig, sezon). Durum kodları: 0/12 = başlamadı, 1/3/5 = canlı (dakika sayısı status_text'te — site `'` işaretini render ederken ekler), 14/15/17 = basketbol periyotları, 20 = uzatma ("UZ"), 4/13 ve "MS" = bitti (Maç Sonu). Skoru boş olan canlı/bitmiş maç 0-0'dır (henüz gol yok). Puan durumu sitenin kendi widget işleyicisinden gelir (`Home/StandingHandler.aspx?league=Tur|Eng|Esp|Ita|Ger`). Aktarım Chrome TLS kimliğine bürünme kullanır (`curl-cffi`, `chrome120`); istekler ~0,8 sn arayla yapılır; her şey salt okunurdur. Not: "Süper Lig" aynı zamanda Yunanistan, İsviçre, Sırbistan, Slovakya, Hindistan ve Endonezya'da da lig adıdır — `country` alanını kontrol edin.

## Kurulum

```bash
uvx mackolik-mcp        # doğrudan çalıştır (uv gerekir)
# veya
pip install mackolik-mcp
mackolik-mcp    # MCP sunucusunu stdio üzerinde başlatır
```

## Testler

```bash
python -m venv .venv && .venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests -v
```

Çevrimdışı testler kayıtlı örnek verilerle çalışır (2026-11-07'den gerçek akış yanıtları); canlı testler mackolik.com'a bağlanır. Derleme anında 26/26 yeşil (14 çevrimdışı + 12 canlı) ve bir MCP stdio duman testi (34 canlı maç, Süper Lig lideri Galatasaray 25 puan).

## Yol haritası

- Gol atanlar / maç olayları (detay sayfası biten maçlarda bunları taşır)
- Basketbol canlı skorları birinci sınıf filtre olarak (sport alanı zaten ayrıştırılıyor)
- Takım sayfalarından karşılıklı maçlar / form durumu

## Lisans

MIT — bkz. [LICENSE](LICENSE).
