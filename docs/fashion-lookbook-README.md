# fashion-lookbook

Tek bir ürün fotoğrafından 10 karelik editöryel lookbook üreten tek dosyalık koşucu.
Motor: **GPT Image 2** (Kie.ai üzerinden). Virtual try-on yok — kıyafet doğrudan
çoklu referans yeteneğiyle üretiliyor.

Üç ürün için koşuldu, üçünde de 10/10 kare çıktı. Toplam 39 üretim çağrısı, ~$1.17.

| | 01 waffle polo | 02 keten gömlek | 03 çizgili gömlek |
|---|---|---|---|
| Girdi | 1 ürün fotoğrafı | 1 ürün fotoğrafı | 3 render (ön/yan/arka) |
| Referans ölçümü | L\* 83.6 · C\*ab 26.5 · h 98.4° | L\* 85.7 · C\*ab 8.7 · h 257.0° | akromatik |
| Model | erkek | kadın | aynı kadın |
| Üretim çağrısı | 12 | 10 | 17 (6'sı test) |
| Hero denemesi | 3 | 1 | 1 |
| Ölçüm sonucu | renk QC 0/10 | renk QC 0/10 | çizgi QC 10/10 |
| Kullanılabilir kare | 10/10 | 10/10 | 10/10 |

## Kullanım

```bash
pip install requests pillow numpy scikit-image scipy
export KIE_API_KEY="..."

cd 03-striped-shirt
python3 run_lookbook.py --check      # ön kontrol, istek atmaz
python3 run_lookbook.py --dry-run    # promptları yazar, istek atmaz
python3 run_lookbook.py --shots 1    # sadece hero
python3 run_lookbook.py              # kalan kareleri üret
python3 stripe_qc.py                 # çizgi geometrisi ölçümü
```

Script idempotent: `out/` içinde var olan kareyi tekrar üretmez, `state.json`
üzerinden yüklenmiş referans URL'lerini ve hero'yu hatırlar. Ağ koptuğunda veya
süreç öldüğünde aynı komutu tekrar çalıştırmak yeterli.

### Ek bayraklar (03)

```bash
--views front            # ablasyon: sadece belirtilen görünümleri gönder
--weighting equal|primary  # referanslar eşit ağırlıklı mı, biri yetkili mi
--suffix _TEST           # çıktıyı ayrı dosya adına yaz, karşılaştırma için
```

## Kare planı

Üç üründe de aynı: 1 hero · 2 yaka+plaket · 3 makro doku · 4 arkadan ·
5–7 PDP · 8 bitim detayı · 9–10 sosyal. Formatlar 2:3, 1:1, 3:4, 4:5, 9:16.

## Öğrenilenler

**Sahne ışığı üründen türetilir, kopyalanmaz.** Ürün 1 açık pastel sarıydı
(C\*ab 26.5): sıcak ışık hardala kaydırır, sert güneş beyaza yakar → nötr ışıklı
üç sahne. Ürün 2 soluk maviydi (C\*ab 8.7): aynı yasaklara ek olarak mavi gökyüzü
ve deniz de eleniyor, çünkü soluk maviye mavi taşırıp hue'yu cyan'a çevirir.
Ürün 3 akromatik — bu yasakların hiçbiri geçerli değildi ama sahneler ürün 2'den
kopyalandı. Sonuç: 02 ve 03 setleri neredeyse aynı görünüyor. Bilinen eksik.

**Ölçüm kutusu ürüne göre konumlanmalı.** Orijinal QC karenin sabit merkezinden
(%35–65 genişlik) örnek alıyordu. Hero prompt'u özneyi sağ üçte bire koyunca kutu
duvara düştü ve kumaş için L\* 62.1 raporladı — gerçek değer 85.7. Ürün 2'de kumaş
renginden maske türetilerek düzeltildi; chroma sapması 10 karenin 9'unda eşiğin
altına indi.

**Eşik ürüne uymuyorsa metrik değil gürültü üretir.** Ürün 2'de dh eşiği 2°'ydi
ama C\* 8.7'de 13°'lik hue dönüşü a\*b\* düzleminde ~2 birim — gözle ayırt edilmez.
Ürün 3'te kırpılma eşiğini %2 koymuştum, referansın kendi değeri %4.6'ydı; eşik
yapısı gereği her kareyi FAIL yapıyordu.

**Çoklu referans bu üründe ölçülebilir fayda vermedi.** Arkadan çekim tek önden
referansla 3 kez üretildi; hiçbirinde sırta plaket veya cep gelmedi, çizgi sapması
%0–5 (üç referanslı hali %5). Sırtı belirgin farklı bir üründe sonuç değişebilir —
ölçülmedi.

**Çoklu referansın öngörülmemiş maliyeti var.** 03'ün 9. karesi ilk üretimde
3 panelli kolaj olarak geldi: model "üç açıdan referans" kurgusunu çıktının
kompozisyonuna taşıdı. Kısıta tek fotoğraf şartı eklendi.

**Sayısal ölçüm kompozisyon hatalarına kör.** O kolajı çizgi ölçümü PASS verdi,
çünkü panellerdeki gömlekler de doğru çizgiliydi. Contact sheet'e bakınca görüldü.
Göz kontrolü metrikle değiştirilemez.

## Dizin yapısı

```
01-waffle-polo/     run_lookbook.py · garment.jpg · out/ · contact_sheet.jpg · qc_report.md
02-linen-shirt/     run_lookbook.py · garment.jpg · out/ · contact_sheet.jpg · qc_report.md
03-striped-shirt/   run_lookbook.py · stripe_qc.py · garment_{front,side,back}.png
                    out/ · out/_ab_test/ · contact_sheet.jpg · stripe_report.md
docs/BRIEF.md       ilk ürünün yürütme yönergesi
```

`03-striped-shirt/out/_ab_test/` karşılaştırma kareleri: referans ağırlığı A/B,
tek referans ablasyonunun üç tekrarı ve kolaj olarak gelen ilk 9. kare.

## API notları

Kie.ai'ın iş sorgulama ucu `POST /api/v1/jobs/createTask` ile başlar,
durum ise **`GET /api/v1/jobs/recordInfo?taskId=...`** ile okunur.
Sonuç URL'i doğrudan gövdede değil, `data.resultJson` içinde gömülü bir JSON
string olarak gelir. `data.param` isteğin kopyasıdır ve girdi referans URL'lerini
içerir — sonuç aranırken atlanmalı, yoksa referans görseli sonuç sanılır.
