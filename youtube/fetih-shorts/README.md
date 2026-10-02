# İstanbul'un Fethi — Shorts

- `metin.md`: seslendirme metni (~50 sn)
- `linkler.txt`: OpenArt'ta üretilen 7 sahne görseli (Seedream 4.5, 9:16)
- `montaj.sh`: görselleri yakınlaştırma/kaydırma efekti ve geçişlerle 1080x1920 videoya çevirir

## Kullanım
```bash
cd youtube/fetih-shorts
while read n url; do curl -sS -o "$n.jpg" "$url"; done < linkler.txt
./montaj.sh ses.mp3   # ses yoksa: ./montaj.sh  (sahne başı 7 sn)
```
Not: görselleri indirmek için ortamın ağ ayarında `cdn.openart.ai` izinli olmalı.
