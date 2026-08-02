#!/usr/bin/env python3
"""
Cizgili gomlek icin olcum takimi.

Bu urun akromatik: siyah + kirik beyaz. Chroma sifira yakin oldugu icin
run_lookbook.py'daki hue/chroma kapilari burada gurultuden ibaret. Anlamli
olan uc sey var ve bu dosya onlari olcer:

  1. CIZGI SIKLIGI  - gomlek govdesine kac cizgi siyor. Olcek-bagimsiz:
     bbox yuksekligine normalize edilir, yani modelin kadrajdaki buyuklugu
     sonucu etkilemez. Referanstan sapma buyukse desen kalinlasmis/incelmis
     demektir - urun yanlis gorunur.
  2. CIZGI ACISI    - cizgiler yatay kalmali. 2B FFT'de baskin tepe noktasinin
     acisi olculur. Buyuk sapma = desen egilmis veya dalgalanmis.
  3. TON ve KIRPILMA - siyah seritler detay korumali, beyaz seritler yanmamali.
     Sertlestirilmis isikta ilk bozulan sey budur.

Kullanim:
    python3 stripe_qc.py                 # out/*.png hepsini olc
    python3 stripe_qc.py a.png b.png     # belirli dosyalari olc
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).parent
REF  = ROOT / "garment_back.png"     # cizgi geometrisi icin en duz genis yuzey

# Kirpma kareleri gomlegin sadece bir parcasini gosterir; "govdeye kac cizgi
# siyor" olcusu onlarda tanimsizdir, ayri raporlanir.
CROP_FRAMES = {"03_detail_stripe", "08_detail_cuff"}


def stripe_box(g: np.ndarray):
    """Cizgili bolgeyi otomatik bul: dikey band-pass enerjisinin en buyuk
    bagli bileseni. Kumas disi (duvar, pantolon, zemin) disarida kalir.

    Hem bbox hem maske doner. bbox FFT icin gerekli (dikdortgen ister), ama
    TON olcumu maskeden yapilir: bbox dikdortgen, gomlek degil - koselerinde
    referansta beyaz fon, karelerde sac ve duvar kalir ve kirpilma sayilarini
    bozar."""
    resp = np.abs(ndimage.gaussian_filter1d(g, 2, axis=0)
                  - ndimage.gaussian_filter1d(g, 6, axis=0))
    energy = ndimage.uniform_filter(resp, 25)
    mask = energy > energy.max() * 0.35
    lab, n = ndimage.label(mask)
    if n == 0:
        return None
    sizes = ndimage.sum(mask, lab, range(1, n + 1))
    comp = lab == int(np.argmax(sizes)) + 1
    ys, xs = np.where(comp)
    box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    return box, comp


def measure(path: Path):
    im = Image.open(path).convert("L")
    g = np.asarray(im).astype(float)
    found = stripe_box(g)
    if found is None:
        return None
    (x0, y0, x1, y1), comp = found
    patch = g[y0:y1, x0:x1]
    fabric = g[comp]                      # ton olcumu icin sadece kumas pikselleri
    h, w = patch.shape
    if h < 40 or w < 40:
        return None

    # --- cizgi sikligi: satir ortalamasi profilinin baskin frekansi
    prof = patch.mean(1)
    prof = (prof - prof.mean()) * np.hanning(len(prof))
    F = np.abs(np.fft.rfft(prof))
    F[:3] = 0                                   # govde golgesi
    cycles = int(np.argmax(F))
    stripes_per_body = cycles                   # bbox = govde -> dogrudan sayi

    # --- cizgi acisi: 2B FFT'de baskin tepe
    win = patch * np.outer(np.hanning(h), np.hanning(w))
    S = np.abs(np.fft.fftshift(np.fft.fft2(win - win.mean())))
    cy, cx = h // 2, w // 2
    S[cy - 2:cy + 3, cx - 2:cx + 3] = 0         # DC civari
    py, px = np.unravel_index(np.argmax(S), S.shape)
    dy, dx = py - cy, px - cx
    # yatay cizgi -> frekans dikey -> dx ~ 0. Sapmayi dereceye cevir.
    angle = abs(np.degrees(np.arctan2(dx, abs(dy) if dy else 1e-9)))

    # --- ton ve kirpilma (sadece kumas pikselleri)
    dark  = float(np.percentile(fabric, 12))
    light = float(np.percentile(fabric, 88))
    clip_hi = float((fabric >= 253).mean() * 100)
    clip_lo = float((fabric <= 2).mean() * 100)

    return dict(name=path.stem, box=(x0, y0, x1, y1), stripes=stripes_per_body,
                angle=angle, dark=dark, light=light,
                contrast=light - dark, clip_hi=clip_hi, clip_lo=clip_lo)


def main():
    args = sys.argv[1:]
    frames = [Path(a) for a in args] if args else sorted((ROOT / "out").glob("*.png"))
    ref = measure(REF)
    if ref is None:
        sys.exit("referans olculemedi")

    print(f"REFERANS ({REF.name})")
    print(f"  cizgi/govde={ref['stripes']}  aci={ref['angle']:.1f}deg  "
          f"siyah={ref['dark']:.0f}  beyaz={ref['light']:.0f}  "
          f"kontrast={ref['contrast']:.0f}  yanik=%{ref['clip_hi']:.1f}  "
          f"tikali=%{ref['clip_lo']:.1f}")
    print(f"  esikler: cizgi sapmasi <=%20 - aci <=8deg - yanik <=%"
          f"{max(ref['clip_hi']*3,5.0):.1f} - tikali <=%{max(ref['clip_lo']*3,15.0):.1f} "
          f"- kontrast >={ref['contrast']*0.55:.0f}\n")

    hdr = (f"{'kare':24s} {'cizgi':>6} {'sapma':>7} {'aci':>6} {'siyah':>6} "
           f"{'beyaz':>6} {'kontr':>6} {'yanik%':>7} {'tikali%':>8}  sonuc")
    print(hdr); print("-" * len(hdr))

    rows = []
    for p in frames:
        m = measure(p)
        if m is None:
            print(f"{p.stem:24s}  olculemedi"); continue
        crop = m["name"] in CROP_FRAMES
        dev = abs(m["stripes"] - ref["stripes"]) / ref["stripes"] * 100
        fails = []
        # Kirpilma esikleri REFERANSA GORELI. Sabit %2 esigi referansin kendi
        # degerinin (%4.6) altinda kaliyordu, yani her kareyi kesin FAIL yapardi.
        hi_lim = max(ref["clip_hi"] * 3, 5.0)
        lo_lim = max(ref["clip_lo"] * 3, 15.0)
        # Aci goruntunun dikeyine gore olculuyor; bu sadece govde dik durdugunda
        # gecerli. Kol/omuz kirpmalarinda uzuv kadrajda capraz uzanir ve cizgiler
        # dogru davranirken bile egik olcum verir - kirpma kareleri muaf.
        if not crop and dev > 20:        fails.append(f"cizgi sikligi %{dev:.0f}")
        if not crop and m["angle"] > 8:  fails.append(f"aci {m['angle']:.0f}deg")
        if m["clip_hi"] > hi_lim:        fails.append(f"beyaz yanik %{m['clip_hi']:.1f}")
        if m["clip_lo"] > lo_lim:        fails.append(f"siyah tikali %{m['clip_lo']:.1f}")
        if m["contrast"] < ref["contrast"] * 0.55:
            fails.append(f"kontrast dusuk {m['contrast']:.0f}")
        verdict = "PASS" if not fails else "FAIL - " + ", ".join(fails)
        note = " (kirpma)" if crop else ""
        print(f"{m['name']:24s} {m['stripes']:6d} {dev:6.0f}% {m['angle']:5.1f} "
              f"{m['dark']:6.0f} {m['light']:6.0f} {m['contrast']:6.0f} "
              f"{m['clip_hi']:6.1f} {m['clip_lo']:7.1f}  {verdict}{note}")
        rows.append((m, fails, crop))

    npass = sum(1 for _, f, _ in rows if not f)
    print(f"\nGECEN: {npass}/{len(rows)}")


if __name__ == "__main__":
    main()
