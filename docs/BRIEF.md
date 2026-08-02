# GÖREV BRIEFI — Attir waffle polo lookbook üretimi

> Bu dosya bir **yürütme yönergesidir**. Baştan sona oku, sonra sırayla uygula.
> Kullanıcıya soru sorma, onay bekleme, alternatif önerme. Adımlar deterministik;
> her karar kuralı burada yazılı. Yazılı olmayan bir durumla karşılaşırsan
> §7 HATA PROTOKOLÜ'ne bak; orada da yoksa dur ve §8 formatında rapor ver.

---

## 1. Amaç

Tek bir ürün fotoğrafından (açık sarı waffle örgü polo tişört), **10 karelik editöryel
lookbook** üret. Görseller e-ticaret ürün sayfası ve sosyal medya için kullanılacak.
Motor: **Kie.ai üzerinden GPT Image 2**. Virtual try-on YOK — kıyafet doğrudan
GPT Image 2'nin çoklu referans yeteneğiyle üretilecek.

Üretim bittiğinde otomatik kalite ölçümü koşulacak ve rapor yazılacak.

**Bitiş tanımı:** `out/` içinde 10 PNG, `qc_report.md`, `contact_sheet.jpg` var
ve §8 formatında bir özet raporladın.

---

## 2. Kesin kurallar

1. **Soru sorma.** Bu brief'te olmayan bir seçim gerekiyorsa §7'ye bak.
2. **`run_lookbook.py` dosyasını EK A'daki haliyle birebir yaz.** İçeriğini
   iyileştirme, yeniden yazma, "daha temiz" hale getirme. Tek istisna §7'de
   açıkça izin verilen düzeltmeler.
3. **Promptları değiştirme.** Script'teki `SHOTS`, `SCENES`, `CHARACTER`,
   `GARMENT_DESC`, `BASE_CONSTRAINTS` sabitleri olduğu gibi kalacak.
4. **API anahtarını dosyaya yazma, log'a basma, koda gömme.** Sadece
   `KIE_API_KEY` ortam değişkeninden okunacak.
5. **Toplam üretim çağrısı 20'yi geçemez.** Sayacı tut. 20'ye ulaşırsan dur ve raporla.
6. Ara adımlarda kullanıcıya uzun açıklama yazma. Komutu çalıştır, çıktıyı oku, devam et.

---

## 3. Ön hazırlık

### 3.1 Çalışma dizini
Bulunduğun dizinde `lookbook/` klasörü oluştur ve içine gir. Tüm iş orada olacak.

### 3.2 Bağımlılıklar
```bash
pip install --quiet requests pillow numpy scikit-image
```
`pip` hata verirse `pip3` dene. `externally-managed-environment` hatası alırsan
sonuna `--break-system-packages` ekle.

### 3.3 Ürün fotoğrafı
Kullanıcının verdiği tişört fotoğrafını `lookbook/garment.jpg` olarak kaydet.
Bu dosya yoksa **hiçbir şey yapma**, §8 formatında "garment.jpg bulunamadı" diye raporla ve dur.

### 3.4 API anahtarı
```bash
export KIE_API_KEY="<kullanicinin_anahtari>"
```
Anahtar ortamda yoksa dur ve kullanıcıdan iste. Bu, brief'teki **tek** izinli soru.

### 3.5 Script
`lookbook/run_lookbook.py` dosyasını **EK A**'daki içerikle oluştur.
Doğrula:
```bash
sha256sum run_lookbook.py
```
Beklenen: `ad6a819e44b9130722940ab2b1a0b4b07a1a408c9b0f0de9b977ed72d1b31f47`

Hash tutmuyorsa dosyayı sil ve tekrar yaz. İkinci denemede de tutmazsa devam et
(satır sonu farkı olabilir), ama §8 raporunda belirt.

---

## 4. Yürütme sırası

Her adımı çalıştır, çıktısını oku, bir sonrakine geç.

### ADIM 1 — Ön kontrol
```bash
python3 run_lookbook.py --check
```
`SONUC: HAZIR` bekleniyor. `EKSIK VAR` çıkarsa eksik satırı oku ve §7'ye bak.

### ADIM 2 — Promptları üret ve göz at
```bash
python3 run_lookbook.py --dry-run
```
İstek atmaz, 10 promptu `logs/prompt_NN.txt` dosyalarına yazar.
Çıktıyı kısaca gözden geçir. **Değiştirme.** Sonraki adıma geç.

### ADIM 3 — Hero kareyi üret
```bash
python3 run_lookbook.py --shots 1
```
Bu, ürünü Kie'ye yükler ve 1. kareyi üretir. Yaklaşık 30–90 saniye.
Sayaç: +1 üretim.

### ADIM 4 — Hero kontrolü (kritik — kalan 9 kare buna bağlı)

`out/01_hero_fullbody.png` dosyasını **görsel olarak aç ve incele**. Şu 5 maddeyi kontrol et:

| # | Kontrol | Geçme koşulu |
|---|---|---|
| K1 | Kişi | Tek kişi var, yüz net, eller normal (5 parmak, deforme değil) |
| K2 | Plaket | Tişörtün ön açıklığında **düğme yok** |
| K3 | Kesim | Tişört **bol/boxy**, vücuda yapışmıyor |
| K4 | Doku | Waffle (kare gözenekli) örgü dokusu görünüyor |
| K5 | Renk | Tişört açık sarı; turuncu/hardal değil, beyaza yanmamış |

Ayrıca sayısal kontrol:
```bash
python3 run_lookbook.py --qc-only
```
`01_hero_fullbody` satırı `PASS` mi bak.

**Karar kuralı — aynen uygula:**

- 5 madde de geçti **ve** QC `PASS` → ADIM 5'e geç.
- Herhangi biri başarısız → şunu çalıştır ve ADIM 4'ü tekrarla:
  ```bash
  rm out/01_hero_fullbody.png && python3 run_lookbook.py --shots 1
  ```
  Sayaç: +1 üretim.
- **En fazla 3 hero denemesi.** 3. denemeden sonra hâlâ geçmiyorsa: en son üretileni
  kabul et, ADIM 5'e geç, §8 raporunda hangi maddelerin başarısız olduğunu yaz.

### ADIM 5 — Kalan 9 kare
```bash
python3 run_lookbook.py
```
Var olan kareleri atlar, 2–10 arasını üretir. Yaklaşık 5–12 dakika.
Sayaç: +9 üretim.

Komut bir karede hata verip durursa: §7'ye bak, düzelt, **aynı komutu tekrar çalıştır**.
Script idempotent — tamamlanmış kareleri tekrar üretmez.

### ADIM 6 — Kapanış
Komut zaten `qc_report.md` ve `contact_sheet.jpg` üretti. Eksikse:
```bash
python3 run_lookbook.py --qc-only
```

`contact_sheet.jpg` dosyasını **aç ve bak**. Kontrol et:
- Aynı kişi 8 karede de aynı kişi mi? (3 ve 8 numaralı karelerde yüz olmayabilir, normal)
- Tişört her karede aynı renk ve aynı kesim mi?
- Gözle görülür bozuk kare var mı? (deforme el, eriyik yüz, ikinci kişi)

Bulgularını §8 raporunda **kare numarası vererek** yaz.

---

## 5. Kareler ne olacak

| # | Sahne | Format | Kullanım |
|---|---|---|---|
| 1 | Ege avlusu, gölge | 2:3 | Hero / IG feed |
| 2 | Ege avlusu, gölge | 2:3 | Yaka + plaket detayı |
| 3 | Makro doku | 1:1 | Kumaş yakın çekim |
| 4 | Ege avlusu, gölge | 2:3 | Arkadan görünüm |
| 5 | Mikro-çimento stüdyo | 3:4 | **PDP ana görsel** |
| 6 | Mikro-çimento stüdyo | 3:4 | PDP ikinci açı |
| 7 | Mikro-çimento stüdyo | 3:4 | PDP orta plan |
| 8 | Mikro-çimento stüdyo | 1:1 | Bitim detayı |
| 9 | Gece flash, sokak | 4:5 | Sosyal |
| 10 | Gece flash, sokak | 9:16 | Story / Reels |

---

## 6. Neden bu ayarlar (değiştirme, ama bil)

Ürünün rengi ölçüldü: **L\* 83.6 · C\*ab 26.5 · h 98.4°** — açık, düşük doygunluklu pastel sarı.

- **Golden hour ve sert güneş bilinçli olarak kullanılmıyor.** Sıcak ışık bu rengi
  hardala kaydırır, parlak güneş beyaza yakar. Sahnelerin üçü de nötr ışıklı.
- **QC'de ΔE00 kullanılmıyor.** Ürünün kendi stüdyo fotoğrafında bile kol ile göğüs
  arasında ΔE00 = 2.27 ölçüldü; ΔE eşiği doğru kareleri reddediyor. Onun yerine
  ışıktan bağımsız olan **chroma ve hue** sıkı tutuluyor, **açıklık** serbest bırakılıyor.
- **Doku gate'i var** çünkü waffle, sıkıştırmanın ve upscale'in ilk sildiği şey.
  Renk ve siluet doğruyken kumaş düz jarseye dönüşebilir; FFT bunu yakalar.

---

## 7. Hata protokolü

Script hataları büyük harfli kodla çıkar. Kodu bul, karşısındaki eylemi uygula.

| Kod / durum | Eylem |
|---|---|
| `KIE_API_KEY ortam degiskeni bos` | Kullanıcıdan anahtar iste. Tek izinli soru. |
| `MISSING_GARMENT` | Dur. §8 raporla. |
| `UPLOAD_FAILED 401` / `403` | Anahtar geçersiz. Dur, kullanıcıya bildir. |
| `UPLOAD_FAILED 402` veya mesajda "credit"/"balance"/"insufficient" | Bakiye yetersiz. Dur, kullanıcıya bildir. |
| `UPLOAD_FAILED` diğer | Bir kez tekrar dene. Yine olmazsa dur ve `logs/upload_response.json` içeriğini raporla. |
| `UPLOAD_NO_URL` | `logs/upload_response.json` dosyasını oku. İçinde yüklenen dosyanın URL'i varsa `state.json` içine `{"garment_url": "<o url>"}` yaz ve devam et. Yoksa dur. |
| `CREATE_TASK_FAILED 400` | Mesajı oku. Script `aspect_ratio` ve `quality` için otomatik geri düşüyor. Başka bir parametre şikâyeti varsa: sadece o parametreyi `create_task` içinden çıkar, tekrar çalıştır. Bu §2.2'nin izinli istisnasıdır. |
| `CREATE_TASK_FAILED 429` | 60 saniye bekle, aynı komutu tekrar çalıştır. En fazla 3 kez. |
| `TASK_FAILED` + mesajda "moderation"/"policy"/"safety"/"blocked" | O kareyi **bir kez** tekrar dene. Yine bloklanırsa o kareyi atla, kalanlara devam et, §8'de belirt. Promptu yumuşatmaya çalışma. |
| `TASK_FAILED` diğer | Aynı komutu tekrar çalıştır. En fazla 2 kez. Sonra o kareyi atla. |
| `TASK_TIMEOUT` | Aynı komutu tekrar çalıştır. En fazla 2 kez. Sonra atla. |
| `TASK_DONE_NO_IMAGE` | API şeması değişmiş. `logs/<taskId>.json` dosyasını oku, görsel URL'ini bul, `find_url` fonksiyonunu o alanı bulacak şekilde düzelt. Bu §2.2'nin izinli istisnasıdır. Düzeltemezsen dur ve log'u raporla. |
| `bilinmeyen durum '<x>'` uyarısı | Bilgilendirme. Script beklemeye devam eder. Müdahale etme. |
| ModuleNotFoundError | Eksik paketi kur, komutu tekrar çalıştır. |
| Ağ hatası / ProxyError | 30 saniye bekle, tekrar dene. 3 başarısız denemeden sonra dur. |

**Genel kural:** takıldığında ilk hamlen hep **aynı komutu tekrar çalıştırmaktır**.
Script durumu `state.json` ve `out/` üzerinden tutar; tekrar çalıştırmak güvenli
ve tamamlanmış işi tekrarlamaz.

---

## 8. Rapor formatı (işin sonunda)

Şu başlıkları bu sırayla, kısa ve sayısal yaz:

```
## Sonuç
Üretilen kare: N/10 · Toplam üretim çağrısı: M · Süre: ~X dk · Tahmini maliyet: $Y
(maliyet = üretim çağrısı × $0.03)

## QC tablosu
<qc_report.md içindeki tabloyu aynen yapıştır>

## Görsel inceleme
Karakter tutarlılığı: <aynı kişi mi, hangi karelerde kaymış>
Ürün tutarlılığı: <renk/kesim/doku hangi karelerde bozulmuş>
Kullanılabilir kareler: <numaralar>
Sorunlu kareler: <numara — sorun>

## Üretilen dosyalar
out/*.png · qc_report.md · contact_sheet.jpg

## Atlanan / başarısız
<varsa kare numarası ve sebep, yoksa "yok">
```

Rapora ek yorum, öneri, sonraki adım listesi ekleme. Kullanıcı isterse sorar.

---

## 9. Yapma

- Promptları "iyileştirme"
- Script'i yeniden yazma veya refactor etme
- Try-on servisi (FASHN, fal, Replicate) ekleme
- Farklı model deneme (Nano Banana, Seedream, Flux)
- Kareleri Photoshop/PIL ile rötuşlama, upscale etme
- Başarısız kareyi "idare eder" diye geçirme — kuralı uygula, raporla
- 20 üretim çağrısını aşma

---

## EK A — `run_lookbook.py` (birebir yaz)

```python
#!/usr/bin/env python3
"""
Lookbook Studio — tek dosyalik uretim kosucusu
Attir butter yellow waffle polo · GPT Image 2 (Kie.ai)

Kullanim:
    pip install requests pillow numpy scikit-image
    export KIE_API_KEY="..."
    python3 run_lookbook.py --check          # on kontrol, istek atmaz
    python3 run_lookbook.py --dry-run        # promptlari yazdirir, istek atmaz
    python3 run_lookbook.py --shots 1        # sadece hero kareyi uret
    python3 run_lookbook.py                  # tum kalan kareleri uret
    python3 run_lookbook.py --qc-only        # uretmeden mevcut ciktilari olc
"""

import argparse, base64, json, os, sys, time
from pathlib import Path

import numpy as np
import requests
from PIL import Image
from skimage import color as skcolor

# ─────────────────────────────────────────────────────────────── AYAR

API_KEY   = os.environ.get("KIE_API_KEY", "").strip()
BASE      = "https://api.kie.ai"
UPLOAD    = "https://kieai.redpandaai.co/api/file-base64-upload"
MODEL_I2I = "gpt-image-2-image-to-image"

ROOT    = Path(__file__).parent
GARMENT = ROOT / "garment.jpg"
OUT     = ROOT / "out";  OUT.mkdir(exist_ok=True)
LOGS    = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
STATE   = ROOT / "state.json"

POLL_INTERVAL = 5
POLL_TIMEOUT  = 420

DONE_STATES = {"success", "completed", "succeeded", "complete", "done", "finished"}
FAIL_STATES = {"fail", "failed", "error", "cancelled", "canceled"}

# ─────────────────────────────────────────── URUN + KARAKTER + SAHNE

GARMENT_DESC = (
    "fine-gauge waffle knit cotton polo shirt, visible thermal waffle grid texture, "
    "matte surface, boxy relaxed fit, drop shoulder, open placket with self-fabric tab "
    "and NO buttons, johnny collar with soft roll, short straight sleeves, straight hem, "
    "colour pale butter yellow with a soft green cast, light-to-mid weight, unlined"
)

CHARACTER = (
    "Man, early 30s, Mediterranean features, warm olive-tan skin, dark tousled "
    "medium-length hair, light stubble, straight dark brows, narrow nose bridge, "
    "defined jawline, calm neutral expression, soft eyes, lean athletic build, "
    "natural shoulders, 182cm"
)

# Bu urunun isik kisiti: L*=83.6, C*ab=26.5 -> acik pastel.
# Sicak sert isik rengi hardala kaydirir, parlak gunes beyaza yakar.
SCENES = {
    "aegean_shade": (
        "whitewashed Aegean courtyard, rough lime-plaster walls, worn stone floor, "
        "a single olive tree, weathered wooden shutters. Late morning, subject fully "
        "in OPEN SHADE, soft north light, large white-wall bounce, neutral 5600K, "
        "absolutely no direct sunlight on the subject or the garment"
    ),
    "microcement": (
        "empty micro-cement studio room, seamless neutral grey wall-to-floor transition. "
        "Large softbox 45 degrees camera left plus white bounce right, flat even key light, "
        "soft contact shadow only, neutral 5500K, no colour cast"
    ),
    "night_flash": (
        "narrow old-town street at night, shuttered storefronts, wet cobblestone. "
        "Direct on-camera flash, hard falloff into deep black background, neutral flash "
        "colour temperature, no warm ambient cast on the garment"
    ),
}

BASE_CONSTRAINTS = (
    "no text, graphics, prints or logos on the garment; no accessories, no watch, "
    "no sunglasses, no bag; natural hands with exactly five fingers; the garment must "
    "stay boxy and relaxed, never fitted or tapered; the placket must stay open and "
    "buttonless; the hem must stay straight, never curved or tailed; the waffle grid "
    "texture must remain clearly visible; no warm orange colour cast on the garment; "
    "the garment must not be blown out to white"
)

SHOTS = [
    dict(n=1,  scene="aegean_shade", ar="2:3", label="hero_fullbody",
         shot="full body, subject mid-stride walking left to right, hands relaxed at sides, "
              "gaze off-camera, unposed and natural",
         cam="85mm f/2.2, eye level, subject at right third, Portra 400 grain"),
    dict(n=2,  scene="aegean_shade", ar="2:3", label="medium_wall",
         shot="waist-up, subject leaning back against the plaster wall, one hand in pocket, "
              "head turned slightly away",
         cam="85mm f/2.0, chest level, collar and placket clearly readable"),
    dict(n=3,  scene="aegean_shade", ar="1:1", label="detail_texture",
         shot="tight macro crop of the shoulder and upper chest area of the garment only, "
              "no face in frame, showing the waffle knit grid, the collar roll and the "
              "shoulder seam in sharp detail",
         cam="100mm macro, f/4, raking soft light to reveal texture relief"),
    dict(n=4,  scene="aegean_shade", ar="2:3", label="back_view",
         shot="full body from behind, subject standing still facing the wall, arms relaxed, "
              "showing the back of the garment, the boxy volume and the straight hem",
         cam="85mm f/2.5, eye level, centred"),
    dict(n=5,  scene="microcement",  ar="3:4", label="pdp_front",
         shot="full body, subject standing straight facing camera, arms relaxed at sides, "
              "neutral expression, catalogue posture",
         cam="50mm f/5.6, chest level, subject centred, full garment visible"),
    dict(n=6,  scene="microcement",  ar="3:4", label="pdp_three_quarter",
         shot="full body, subject turned three-quarters to camera left, arms relaxed, "
              "catalogue posture",
         cam="50mm f/5.6, chest level, subject centred"),
    dict(n=7,  scene="microcement",  ar="3:4", label="pdp_medium",
         shot="chest to hip crop, subject facing camera, showing how the garment sits "
              "on the body, the placket and the hem line",
         cam="85mm f/5.6, flat even light"),
    dict(n=8,  scene="microcement",  ar="1:1", label="detail_finish",
         shot="close crop showing the short sleeve opening and the straight bottom hem "
              "of the garment, no face in frame",
         cam="100mm macro f/5.6, even light"),
    dict(n=9,  scene="night_flash",  ar="4:5", label="social_candid",
         shot="medium shot, subject caught mid-laugh looking slightly off camera, candid "
              "snapshot energy, slight motion in the frame",
         cam="35mm f/4, hip level, slight tilt, direct flash"),
    dict(n=10, scene="night_flash",  ar="9:16", label="social_vertical",
         shot="full body, subject walking towards camera at night, candid snapshot, "
              "leave the top 15 percent and bottom 20 percent of the frame uncluttered "
              "for social media UI overlays",
         cam="35mm f/4, waist level, direct flash"),
]


def build_prompt(shot, with_hero: bool) -> str:
    ident = (
        "Reference image 1 is the GARMENT product photo - reproduce this exact garment: "
        "its colour, its waffle texture, its cut and its proportions.\n"
        "Reference image 2 is the SAME MODEL from an earlier frame of this shoot - keep "
        "IDENTICAL facial identity: same eye shape, same nose bridge contour, same jawline "
        "angle, same hairline, same stubble density, same skin tone.\n"
        if with_hero else
        "Reference image 1 is the GARMENT product photo - reproduce this exact garment: "
        "its colour, its waffle texture, its cut and its proportions.\n"
    )
    return (
        f"Goal: editorial fashion lookbook frame {shot['n']} of 10, for e-commerce and social media.\n"
        f"{ident}"
        f"Subject: {CHARACTER}, wearing the garment.\n"
        f"Garment: {GARMENT_DESC}\n"
        f"Scene: {SCENES[shot['scene']]}\n"
        f"Shot: {shot['shot']}\n"
        f"Camera: {shot['cam']}\n"
        f"Style: photorealistic editorial fashion photography, shot on film, "
        f"natural skin texture, no beauty retouching, no plastic skin\n"
        f"Preserve: exact garment colour and waffle texture from reference image 1"
        f"{', exact facial identity from reference image 2' if with_hero else ''}\n"
        f"Constraints: {BASE_CONSTRAINTS}"
    )


# ─────────────────────────────────────────────────────────── KIE API

def hdrs():
    if not API_KEY:
        sys.exit("HATA: KIE_API_KEY ortam degiskeni bos.\n"
                 '  export KIE_API_KEY="..." ile ayarla.')
    return {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


def find_url(obj):
    """Yanit semasi surume gore degisebiliyor; JSON icinde ilk gecerli URL'yi bul."""
    hits = []
    def walk(o):
        if isinstance(o, str) and o.startswith("http"):
            hits.append(o)
        elif isinstance(o, dict):
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
        elif isinstance(o, str):
            pass
    walk(obj)
    for h in hits:
        if any(h.lower().split("?")[0].endswith(e) for e in (".png", ".jpg", ".jpeg", ".webp")):
            return h
    return hits[0] if hits else None


def upload_garment(path: Path) -> str:
    b64 = base64.b64encode(path.read_bytes()).decode()
    body = {
        "base64Data": f"data:image/jpeg;base64,{b64}",
        "uploadPath": "images/lookbook",
        "fileName": "attir_waffle_polo.jpg",
    }
    r = requests.post(UPLOAD, headers=hdrs(), json=body, timeout=180)
    (LOGS / "upload_response.json").write_text(r.text)
    if r.status_code >= 400:
        sys.exit(f"UPLOAD_FAILED {r.status_code}: {r.text[:800]}")
    url = find_url(r.json())
    if not url:
        sys.exit(f"UPLOAD_NO_URL: {r.text[:800]}")
    print(f"  + urun yuklendi -> {url}")
    return url


def create_task(prompt: str, refs: list, ar: str) -> str:
    def _post(aspect):
        body = {"model": MODEL_I2I,
                "input": {"prompt": prompt, "input_urls": refs,
                          "aspect_ratio": aspect, "quality": "high"}}
        return requests.post(f"{BASE}/api/v1/jobs/createTask",
                             headers=hdrs(), json=body, timeout=120)

    r = _post(ar)
    if r.status_code >= 400 and "aspect" in r.text.lower():
        print(f"    ! aspect_ratio '{ar}' reddedildi, 'auto' ile tekrar deneniyor")
        r = _post("auto")
    if r.status_code >= 400 and "quality" in r.text.lower():
        print("    ! quality reddedildi, parametresiz tekrar deneniyor")
        body = {"model": MODEL_I2I,
                "input": {"prompt": prompt, "input_urls": refs, "aspect_ratio": "auto"}}
        r = requests.post(f"{BASE}/api/v1/jobs/createTask",
                          headers=hdrs(), json=body, timeout=120)
    if r.status_code >= 400:
        sys.exit(f"CREATE_TASK_FAILED {r.status_code}: {r.text[:800]}")

    j = r.json()
    tid = (j.get("data") or {}).get("taskId") or j.get("taskId")
    if not tid:
        sys.exit(f"CREATE_TASK_NO_ID: {json.dumps(j)[:800]}")
    return tid


def wait_task(task_id: str) -> str:
    t0, last, warned = time.time(), "", False
    while time.time() - t0 < POLL_TIMEOUT:
        r = requests.get(f"{BASE}/api/v1/jobs/getTask",
                         headers=hdrs(), params={"taskId": task_id}, timeout=60)
        j = r.json()
        (LOGS / f"{task_id}.json").write_text(json.dumps(j, indent=2))
        data = j.get("data") or {}
        state = str(data.get("state") or data.get("status") or "").lower()
        if state != last:
            print(f"    . {state or '(bos)'} ({int(time.time()-t0)}s)")
            last = state
        if state in DONE_STATES:
            url = find_url(data)
            if url and not url.endswith((".jpg", ".jpeg", ".png", ".webp")) and "http" not in url:
                url = None
            if url:
                return url
            sys.exit(f"TASK_DONE_NO_IMAGE: {json.dumps(j)[:1200]}")
        if state in FAIL_STATES:
            sys.exit(f"TASK_FAILED: {json.dumps(j)[:1200]}")
        if state and state not in DONE_STATES | FAIL_STATES \
           and state not in ("pending", "waiting", "queuing", "queued", "running",
                             "processing", "generating", "in_progress") and not warned:
            print(f"    ! bilinmeyen durum '{state}' - beklemeye devam, log: logs/{task_id}.json")
            warned = True
        time.sleep(POLL_INTERVAL)
    sys.exit(f"TASK_TIMEOUT ({POLL_TIMEOUT}s): {task_id}")


def download(url: str, dest: Path):
    r = requests.get(url, timeout=300); r.raise_for_status()
    dest.write_bytes(r.content)
    print(f"  + {dest.name}  ({len(r.content)//1024} KB)")


# ────────────────────────────────────────────────────────────── QC

def garment_lab(path: Path, box=None):
    im = Image.open(path).convert("RGB")
    W, H = im.size
    if box is None:
        box = (int(W*0.35), int(H*0.35), int(W*0.65), int(H*0.60))
    patch = np.asarray(im.crop(box)).astype(np.float64) / 255.0
    med = np.median(patch.reshape(-1, 3), axis=0)
    lab = skcolor.rgb2lab(med.reshape(1, 1, 3)).reshape(3)

    g = np.asarray(im.crop(box).convert("L")).astype(np.float64) / 255.0
    F = np.abs(np.fft.fftshift(np.fft.fft2(g - g.mean())))
    cy, cx = np.array(F.shape) // 2
    yy, xx = np.ogrid[:F.shape[0], :F.shape[1]]
    rad = np.hypot(yy - cy, xx - cx)
    rmax = min(cy, cx)
    hi = F[(rad > rmax*0.25) & (rad <= rmax*0.85)].sum()
    tot = F[rad > 2].sum()
    return lab, (hi / tot if tot else 0.0)


def qc_rows(ref_path: Path, frames: list):
    ref_lab, ref_tex = garment_lab(ref_path)
    rC = float(np.hypot(ref_lab[1], ref_lab[2]))
    rh = float(np.degrees(np.arctan2(ref_lab[2], ref_lab[1])) % 360)
    out = []
    for p in frames:
        lab, tex = garment_lab(p)
        C = float(np.hypot(lab[1], lab[2]))
        h = float(np.degrees(np.arctan2(lab[2], lab[1])) % 360)
        rec = dict(name=p.stem, L=lab[0], C=C, h=h,
                   dC=abs(C-rC), dh=abs((h-rh+180) % 360 - 180),
                   dL=abs(lab[0]-ref_lab[0]),
                   tex=(tex/ref_tex if ref_tex else 0.0))
        f = []
        if rec["dC"]  > 2.0:  f.append(f"chroma dC={rec['dC']:.1f}")
        if rec["dh"]  > 2.0:  f.append(f"hue dh={rec['dh']:.1f}deg")
        if rec["dL"]  > 10.0: f.append(f"aciklik dL={rec['dL']:.1f}")
        if rec["L"]   > 92:   f.append(f"beyaza yanma L*={rec['L']:.0f}")
        if rec["tex"] < 0.70: f.append(f"doku kaybi {rec['tex']:.2f}")
        rec["fails"] = f
        rec["pass"] = not f
        out.append(rec)
    return (ref_lab, rC, rh, ref_tex), out


def qc_report(ref_path: Path, frames: list) -> str:
    (ref_lab, rC, rh, _), rows = qc_rows(ref_path, frames)
    body = [f"| {r['name']} | {r['L']:.1f} | {r['C']:.1f} | {r['h']:.1f} | {r['dC']:.2f} | "
            f"{r['dh']:.2f} | {r['dL']:.1f} | {r['tex']:.2f} | "
            f"{'PASS' if r['pass'] else '**FAIL** - ' + ', '.join(r['fails'])} |" for r in rows]
    npass = sum(r["pass"] for r in rows)
    return "\n".join([
        "# QC raporu - Attir waffle polo lookbook", "",
        f"Referans (urun fotografi): **L\\* {ref_lab[0]:.1f} - C\\*ab {rC:.1f} - h {rh:.1f}deg**", "",
        "Esikler: `dC*ab <= 2.0` - `dh <= 2.0deg` - `dL* <= 10` - `L* <= 92` - `doku orani >= 0.70`", "",
        "| kare | L* | C*ab | h(deg) | dC | dh | dL | doku | sonuc |",
        "|---|---|---|---|---|---|---|---|---|",
        *body, "",
        f"**Gecen: {npass}/{len(rows)}**", "",
        "_Not: olcum karenin merkez kutusundan aliniyor. Segmentasyon (SAM3) eklendiginde "
        "sadece kumas bolgesi olculerek dogruluk artar._",
    ])


def contact_sheet(frames: list, dest: Path, cols=5, cell=420):
    if not frames: return
    rows = (len(frames) + cols - 1) // cols
    sheet = Image.new("RGB", (cols*cell, rows*cell), "#EFEFEF")
    for i, p in enumerate(frames):
        im = Image.open(p).convert("RGB")
        im.thumbnail((cell-12, cell-12))
        x = (i % cols)*cell + (cell - im.width)//2
        y = (i//cols)*cell + (cell - im.height)//2
        sheet.paste(im, (x, y))
    sheet.save(dest, quality=92)
    print(f"  + {dest.name}")


# ───────────────────────────────────────────────────────────── MAIN

def preflight():
    ok = True
    print("ON KONTROL")
    print(f"  KIE_API_KEY        : {'var (' + str(len(API_KEY)) + ' karakter)' if API_KEY else 'YOK'}")
    ok &= bool(API_KEY)
    print(f"  garment.jpg        : {'var' if GARMENT.exists() else 'YOK'}")
    ok &= GARMENT.exists()
    for host in (BASE, UPLOAD.rsplit("/api", 1)[0]):
        try:
            c = requests.get(host, timeout=15).status_code
            print(f"  {host:34s}: HTTP {c}")
        except Exception as e:
            print(f"  {host:34s}: ULASILAMADI ({type(e).__name__})")
            ok = False
    if GARMENT.exists():
        lab, tex = garment_lab(GARMENT)
        print(f"  referans olcum     : L*={lab[0]:.1f} C*ab={np.hypot(lab[1],lab[2]):.1f} "
              f"h={np.degrees(np.arctan2(lab[2],lab[1]))%360:.1f}deg doku={tex:.3f}")
    print("SONUC:", "HAZIR" if ok else "EKSIK VAR")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", nargs="*", type=int)
    ap.add_argument("--qc-only", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    if a.check:
        sys.exit(0 if preflight() else 1)

    picked = [s for s in SHOTS if not a.shots or s["n"] in a.shots]

    if a.dry_run:
        for s in picked:
            print("=" * 70)
            print(f"SHOT {s['n']} - {s['label']}  [{s['ar']}]")
            print("=" * 70)
            p = build_prompt(s, with_hero=(s["n"] != 1))
            (LOGS / f"prompt_{s['n']:02d}.txt").write_text(p)
            print(p, "\n")
        return

    if not a.qc_only:
        if not GARMENT.exists():
            sys.exit(f"MISSING_GARMENT: {GARMENT}")

        state = json.loads(STATE.read_text()) if STATE.exists() else {}
        print("-> urun yukleniyor")
        garment_url = state.get("garment_url") or upload_garment(GARMENT)
        state["garment_url"] = garment_url
        STATE.write_text(json.dumps(state, indent=2))
        hero_url = state.get("hero_url")

        for s in sorted(picked, key=lambda s: (s["n"] != 1, s["n"])):
            dest = OUT / f"{s['n']:02d}_{s['label']}.png"
            if dest.exists():
                print(f"-> shot {s['n']} zaten var, atlaniyor")
                continue
            with_hero = s["n"] != 1 and bool(hero_url)
            refs = [garment_url] + ([hero_url] if with_hero else [])
            if s["n"] != 1 and not hero_url:
                print(f"  ! shot {s['n']}: hero yok, yuz tutarliligi olmadan uretiliyor")
            print(f"-> shot {s['n']} ({s['label']}, {s['ar']}, {len(refs)} referans)")
            prompt = build_prompt(s, with_hero)
            (LOGS / f"prompt_{s['n']:02d}.txt").write_text(prompt)
            url = wait_task(create_task(prompt, refs, s["ar"]))
            download(url, dest)
            if s["n"] == 1:
                hero_url = url
                state["hero_url"] = url
                STATE.write_text(json.dumps(state, indent=2))

    frames = sorted(OUT.glob("*.png"))
    if not frames:
        print("Olculecek cikti yok."); return
    print("-> QC olcumu")
    (ROOT / "qc_report.md").write_text(qc_report(GARMENT, frames))
    print("  + qc_report.md")
    contact_sheet(frames, ROOT / "contact_sheet.jpg")
    _, rows = qc_rows(GARMENT, frames)
    print(f"\nGECEN: {sum(r['pass'] for r in rows)}/{len(rows)}")
    for r in rows:
        if not r["pass"]:
            print(f"  FAIL {r['name']}: {', '.join(r['fails'])}")


if __name__ == "__main__":
    main()
```
