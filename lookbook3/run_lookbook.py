#!/usr/bin/env python3
"""
Lookbook Studio — tek dosyalik uretim kosucusu
Powder blue washed linen shirt · GPT Image 2 (Kie.ai)

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

# Urunun uc gorunumu. Sira ONEMLI: prompt'ta "reference image N" diye
# numarayla atif yapiliyor ve her kare hangi gorunumu baz alacagini soyluyor.
VIEWS = [
    ("front", ROOT / "garment_front.png", "straight-on FRONT view: the authority for the "
     "stripe colours, the stripe width and pitch, the button placket and the chest pocket"),
    ("side",  ROOT / "garment_side.png",  "SIDE view: the authority for the sleeve line, "
     "the side seam and the shoulder volume"),
    ("back",  ROOT / "garment_back.png",  "BACK view: the authority for the back collar, "
     "the yoke and the curved back hem"),
]
GARMENT = VIEWS[0][1]      # renk/doku olcumu ve QC referansi hep onden gorunum
OUT     = ROOT / "out";  OUT.mkdir(exist_ok=True)
LOGS    = ROOT / "logs"; LOGS.mkdir(exist_ok=True)
STATE   = ROOT / "state.json"

POLL_INTERVAL = 5
POLL_TIMEOUT  = 420

DONE_STATES = {"success", "completed", "succeeded", "complete", "done", "finished"}
FAIL_STATES = {"fail", "failed", "error", "cancelled", "canceled"}

# ─────────────────────────────────────────── URUN + KARAKTER + SAHNE

GARMENT_DESC = (
    "horizontally striped shirt in even black and warm off-white stripes of equal width, "
    "crisp light cotton with a smooth matte surface, softly relaxed fit, classic pointed "
    "collar, full-length button placket with dark tonal buttons, one patch pocket on the "
    "left chest, long sleeves with buttoned barrel cuffs, curved shirttail hem dropping "
    "longer at the back, unlined"
)

CHARACTER = (
    "Woman, early 30s, Southern European features, light olive skin, dark brown "
    "shoulder-length hair loosely tucked behind one ear, fine straight brows, soft "
    "almond eyes, high cheekbones, straight nose, calm neutral expression, minimal "
    "natural makeup, slim build, natural shoulders, 175cm"
)

# Bu urun akromatik: siyah + kirik beyaz. Renk kaymasi riski yok, asil risk
# KONTRAST ve CIZGI GEOMETRISI. Sert isik beyaz seritleri yakar, siyahlari
# tikar; ince seritler ise kadrajda moire ve dalgalanma uretir.
SCENES = {
    "daylight_room": (
        "quiet empty room with off-white plaster walls and a pale grey stone floor, one tall "
        "window with a sheer white curtain. Soft diffused north daylight, large white bounce, "
        "neutral 5600K, no direct sun patch on the subject, gentle contrast that keeps detail "
        "in both the white and the black stripes"
    ),
    "studio_seamless": (
        "empty studio, seamless mid-grey paper sweep, wall-to-floor transition. Large softbox "
        "45 degrees camera left plus white bounce right, flat even key light, soft contact "
        "shadow only, neutral 5500K, no colour cast, no specular hotspots on the fabric"
    ),
    "overcast_terrace": (
        "old stone terrace under a fully overcast white sky, weathered pale limestone paving "
        "and a low plaster parapet. Soft shadowless overcast light, neutral 5600K, "
        "no blown highlights on the white stripes"
    ),
}

BASE_CONSTRAINTS = (
    "no text, graphics, prints or logos on the garment; no accessories, no watch, "
    "no sunglasses, no bag, no jewellery; natural hands with exactly five fingers; "
    "the stripes must stay horizontal, straight, parallel and even in width, following the "
    "curve of the body without wobbling, warping or moire; the stripe pitch must match the "
    "references and must not become finer or coarser; the stripes must stay black and warm "
    "off-white, never grey, blue or sepia; the shirt must stay buttoned with the placket "
    "visible and the collar sitting flat; exactly one patch pocket, on the left chest, and "
    "no pocket anywhere else; the sleeves must stay long with the cuffs buttoned at the "
    "wrist, never rolled up; the curved shirttail hem must remain curved, never cut straight; "
    "the white stripes must not blow out to pure white and the black stripes must keep "
    "some detail"
)

SHOTS = [
    dict(n=1,  scene="daylight_room", ar="2:3", label="hero_fullbody", primary=1,
         shot="full body, subject mid-stride walking left to right past the window, hands "
              "relaxed at sides, gaze off-camera, unposed and natural",
         cam="85mm f/2.2, eye level, subject at right third, Portra 400 grain"),
    dict(n=2,  scene="daylight_room", ar="2:3", label="medium_collar", primary=1,
         shot="waist-up, subject standing near the window turned slightly to the light, one "
              "hand at her side, head turned a little away, collar, button placket and the "
              "left chest pocket clearly readable",
         cam="85mm f/2.0, chest level, collar and placket in focus"),
    dict(n=3,  scene="daylight_room", ar="1:1", label="detail_stripe", primary=1,
         shot="tight macro crop of the shoulder and upper chest of the garment only, no face "
              "in frame, showing the stripe pitch, how the stripes meet at the shoulder seam "
              "and how they run across the placket",
         cam="100mm macro, f/4, soft even light"),
    dict(n=4,  scene="daylight_room", ar="2:3", label="back_view", primary=3,
         shot="full body from behind, subject standing still facing the wall, arms relaxed, "
              "showing the back of the shirt, the yoke, how the stripes run across the back "
              "and the curved shirttail hem dropping longer at the back",
         cam="85mm f/2.5, eye level, centred"),
    dict(n=5,  scene="studio_seamless",  ar="3:4", label="pdp_front", primary=1,
         shot="full body, subject standing straight facing camera, arms relaxed at sides, "
              "neutral expression, catalogue posture",
         cam="50mm f/5.6, chest level, subject centred, full garment visible"),
    dict(n=6,  scene="studio_seamless",  ar="3:4", label="pdp_three_quarter", primary=2,
         shot="full body, subject turned three-quarters to camera left, arms relaxed, "
              "catalogue posture",
         cam="50mm f/5.6, chest level, subject centred"),
    dict(n=7,  scene="studio_seamless",  ar="3:4", label="pdp_medium", primary=1,
         shot="crop from collarbone to mid-thigh, head and face completely out of frame, "
              "subject facing camera, showing how the shirt sits on the body, the button "
              "placket, the chest pocket and the full curved hem line",
         cam="85mm f/5.6, flat even light"),
    dict(n=8,  scene="studio_seamless",  ar="1:1", label="detail_cuff", primary=2,
         shot="close crop of the forearm showing the buttoned barrel cuff, the sleeve placket "
              "and how the stripes wrap around the sleeve, no face in frame",
         cam="100mm macro f/5.6, even light"),
    dict(n=9,  scene="overcast_terrace",  ar="4:5", label="social_candid", primary=1,
         shot="medium shot, subject caught mid-laugh looking slightly off camera, candid "
              "snapshot energy, hair catching a little wind",
         cam="35mm f/4, hip level, slight tilt, available overcast light"),
    dict(n=10, scene="overcast_terrace",  ar="9:16", label="social_vertical", primary=1,
         shot="full body, subject walking towards camera across the terrace, candid snapshot, "
              "leave the top 15 percent and bottom 20 percent of the frame uncluttered "
              "for social media UI overlays",
         cam="35mm f/4, waist level, available overcast light"),
]


def build_prompt(shot, with_hero: bool, weighting: str = "equal") -> str:
    lines = [f"Reference image {i+1} is the same garment, {desc}."
             for i, (_, _, desc) in enumerate(VIEWS)]
    if weighting == "primary":
        lines.append(
            f"All {len(VIEWS)} garment references show ONE single garment from different angles - "
            f"reproduce that exact garment: its colours, its stripe geometry, its cut and its "
            f"proportions. For this frame, reference image {shot.get('primary', 1)} is the "
            f"authority; use the others only to resolve what that view does not show."
        )
    else:
        lines.append(
            f"All {len(VIEWS)} garment references show ONE single garment photographed from "
            f"{len(VIEWS)} angles, and together they define it completely. Give them equal "
            f"weight: whatever part of the garment this frame shows, take it from whichever "
            f"reference shows that part. Do not invent or imagine any part of the garment, and "
            f"do not carry a detail onto a side of the garment where the references do not "
            f"show it."
        )
    if with_hero:
        lines.append(
            f"Reference image {len(VIEWS)+1} is the SAME MODEL from an earlier frame of this "
            f"shoot - keep IDENTICAL facial identity: same eye shape, same nose bridge contour, "
            f"same jawline angle, same hairline, same brow shape, same skin tone, same hair length."
        )
    ident = "\n".join(lines) + "\n"
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
        f"Preserve: exact stripe colours, stripe width and stripe pitch from reference image 1"
        f"{f', exact facial identity from reference image {len(VIEWS)+1}' if with_hero else ''}\n"
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
            for k, v in o.items():
                # 'param' istegin kopyasi; icindeki referans URL'leri sonucla karisir
                if k == "param": continue
                walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
        elif isinstance(o, str):
            pass
    # sonuc URL'i 'resultJson' icinde gomulu bir JSON string olarak geliyor
    if isinstance(obj, dict) and isinstance(obj.get("resultJson"), str):
        try:
            obj = {**obj, "resultJson": json.loads(obj["resultJson"])}
        except Exception:
            pass
    walk(obj)
    for h in hits:
        if any(h.lower().split("?")[0].endswith(e) for e in (".png", ".jpg", ".jpeg", ".webp")):
            return h
    return hits[0] if hits else None


def upload_garment(path: Path) -> str:
    b64 = base64.b64encode(path.read_bytes()).decode()
    mime = "png" if path.suffix.lower() == ".png" else "jpeg"
    body = {
        "base64Data": f"data:image/{mime};base64,{b64}",
        "uploadPath": "images/lookbook",
        "fileName": path.name,
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
        r = requests.get(f"{BASE}/api/v1/jobs/recordInfo",
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

def _texture(im: Image.Image, box) -> float:
    g = np.asarray(im.crop(box).convert("L")).astype(np.float64) / 255.0
    F = np.abs(np.fft.fftshift(np.fft.fft2(g - g.mean())))
    cy, cx = np.array(F.shape) // 2
    yy, xx = np.ogrid[:F.shape[0], :F.shape[1]]
    rad = np.hypot(yy - cy, xx - cx)
    rmax = min(cy, cx)
    hi = F[(rad > rmax*0.25) & (rad <= rmax*0.85)].sum()
    tot = F[rad > 2].sum()
    return hi / tot if tot else 0.0


def garment_lab(path: Path, ref_h=None):
    """Kumas bolgesini olcer.

    ref_h yoksa (urun fotografi) karenin merkez kutusu kullanilir - stüdyo
    fotografinda kumas zaten ortadadir. ref_h varsa (uretilen kare) kumas
    RENGINDEN bulunur: sabit merkez kutusu ozne kadrajin kenarindayken arka
    plani olcuyordu. Maske 'kromatik ve referans hue'nun +-60 derecesinde'
    diye tanimli - ten, bej pantolon ve notr duvar disarida kalir, ama band
    gercek bir renk kaymasini yakalayacak kadar genis. Kaplama orani da
    donuyor: kumas beyaza yandiginda veya griye dustugunde maske kuculur,
    bu da basli basina bir sinyaldir.
    """
    im = Image.open(path).convert("RGB")
    W, H = im.size

    if ref_h is None:
        box = (int(W*0.35), int(H*0.35), int(W*0.65), int(H*0.60))
        patch = np.asarray(im.crop(box)).astype(np.float64) / 255.0
        med = np.median(patch.reshape(-1, 3), axis=0)
        lab = skcolor.rgb2lab(med.reshape(1, 1, 3)).reshape(3)
        return lab, _texture(im, box), 1.0

    full = skcolor.rgb2lab(np.asarray(im).astype(np.float64) / 255.0)
    C = np.hypot(full[:, :, 1], full[:, :, 2])
    h = np.degrees(np.arctan2(full[:, :, 2], full[:, :, 1])) % 360
    mask = (C > 2.0) & (np.abs((h - ref_h + 180) % 360 - 180) <= 60.0)
    mask[:int(H*0.05), :] = mask[int(H*0.95):, :] = False   # kenar payi
    mask[:, :int(W*0.05)] = mask[:, int(W*0.95):] = False

    cover = mask.sum() / mask.size
    if cover < 0.01:                       # kumas bulunamadi -> eski yonteme dus
        box = (int(W*0.35), int(H*0.35), int(W*0.65), int(H*0.60))
        patch = np.asarray(im.crop(box)).astype(np.float64) / 255.0
        med = np.median(patch.reshape(-1, 3), axis=0)
        return skcolor.rgb2lab(med.reshape(1, 1, 3)).reshape(3), _texture(im, box), cover

    lab = np.median(full[mask], axis=0)
    ys, xs = np.where(mask)
    box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    return lab, _texture(im, box), cover


def qc_rows(ref_path: Path, frames: list):
    ref_lab, ref_tex, _ = garment_lab(ref_path)
    rC = float(np.hypot(ref_lab[1], ref_lab[2]))
    rh = float(np.degrees(np.arctan2(ref_lab[2], ref_lab[1])) % 360)
    out = []
    for p in frames:
        lab, tex, cover = garment_lab(p, ref_h=rh)
        C = float(np.hypot(lab[1], lab[2]))
        h = float(np.degrees(np.arctan2(lab[2], lab[1])) % 360)
        rec = dict(name=p.stem, L=lab[0], C=C, h=h, cover=cover,
                   dC=abs(C-rC), dh=abs((h-rh+180) % 360 - 180),
                   dL=abs(lab[0]-ref_lab[0]),
                   tex=(tex/ref_tex if ref_tex else 0.0))
        f = []
        if cover < 0.01:      f.append(f"kumas bulunamadi (kaplama {cover*100:.1f}%)")
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
            f"{r['dh']:.2f} | {r['dL']:.1f} | {r['tex']:.2f} | {r['cover']*100:.0f}% | "
            f"{'PASS' if r['pass'] else '**FAIL** - ' + ', '.join(r['fails'])} |" for r in rows]
    npass = sum(r["pass"] for r in rows)
    return "\n".join([
        "# QC raporu - powder blue linen shirt lookbook", "",
        f"Referans (urun fotografi): **L\\* {ref_lab[0]:.1f} - C\\*ab {rC:.1f} - h {rh:.1f}deg**", "",
        "Esikler: `dC*ab <= 2.0` - `dh <= 2.0deg` - `dL* <= 10` - `L* <= 92` - `doku orani >= 0.70`", "",
        "| kare | L* | C*ab | h(deg) | dC | dh | dL | doku | kaplama | sonuc |",
        "|---|---|---|---|---|---|---|---|---|---|",
        *body, "",
        f"**Gecen: {npass}/{len(rows)}**", "",
        "_Not: olcum kumas renginden turetilen maskeden aliniyor; arka plan, ten ve alt "
        "parca disarida. Kaplama = maskenin kare alanina orani, kumasin ne kadarinin "
        "olculdugunu gosterir. Segmentasyon (SAM3) ile maske daha da keskinlesir._",
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
        lab, tex, _ = garment_lab(GARMENT)
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
    ap.add_argument("--weighting", choices=["equal","primary"], default="equal")
    ap.add_argument("--suffix", default="")
    a = ap.parse_args()

    if a.check:
        sys.exit(0 if preflight() else 1)

    picked = [s for s in SHOTS if not a.shots or s["n"] in a.shots]

    if a.dry_run:
        for s in picked:
            print("=" * 70)
            print(f"SHOT {s['n']} - {s['label']}  [{s['ar']}]")
            print("=" * 70)
            p = build_prompt(s, with_hero=(s["n"] != 1), weighting=a.weighting)
            (LOGS / f"prompt_{s['n']:02d}.txt").write_text(p)
            print(p, "\n")
        return

    if not a.qc_only:
        missing = [p for _, p, _ in VIEWS if not p.exists()]
        if missing:
            sys.exit(f"MISSING_GARMENT: {', '.join(str(m) for m in missing)}")

        state = json.loads(STATE.read_text()) if STATE.exists() else {}
        urls = state.get("garment_urls") or {}
        for name, path, _ in VIEWS:
            if name not in urls:
                print(f"-> urun yukleniyor ({name})")
                urls[name] = upload_garment(path)
        state["garment_urls"] = urls
        STATE.write_text(json.dumps(state, indent=2))
        garment_urls = [urls[name] for name, _, _ in VIEWS]
        hero_url = state.get("hero_url")

        for s in sorted(picked, key=lambda s: (s["n"] != 1, s["n"])):
            dest = OUT / f"{s['n']:02d}_{s['label']}{a.suffix}.png"
            if dest.exists():
                print(f"-> shot {s['n']} zaten var, atlaniyor")
                continue
            with_hero = s["n"] != 1 and bool(hero_url)
            refs = garment_urls + ([hero_url] if with_hero else [])
            if s["n"] != 1 and not hero_url:
                print(f"  ! shot {s['n']}: hero yok, yuz tutarliligi olmadan uretiliyor")
            print(f"-> shot {s['n']} ({s['label']}, {s['ar']}, {len(refs)} referans)")
            prompt = build_prompt(s, with_hero, a.weighting)
            (LOGS / f"prompt_{s['n']:02d}{a.suffix}.txt").write_text(prompt)
            url = wait_task(create_task(prompt, refs, s["ar"]))
            download(url, dest)
            if s["n"] == 1:
                hero_url = url
                state["hero_url"] = url
                STATE.write_text(json.dumps(state, indent=2))

    frames = sorted(OUT.glob("*.png"))
    if not frames:
        print("Olculecek cikti yok."); return
    contact_sheet(frames, ROOT / "contact_sheet.jpg")
    # Renk QC'si bu urunde tanimsiz: siyah+beyaz akromatik, chroma ~0 oldugu icin
    # hue gurultuden ibaret. Sadece --qc-only ile acikca istenirse kosar.
    if a.qc_only:
        print("-> QC olcumu")
        (ROOT / "qc_report.md").write_text(qc_report(GARMENT, frames))
        print("  + qc_report.md")
        _, rows = qc_rows(GARMENT, frames)
        print(f"\nGECEN: {sum(r['pass'] for r in rows)}/{len(rows)}")
        for r in rows:
            if not r["pass"]:
                print(f"  FAIL {r['name']}: {', '.join(r['fails'])}")


if __name__ == "__main__":
    main()
