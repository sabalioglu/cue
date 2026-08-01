# QC raporu - powder blue linen shirt lookbook

Referans (urun fotografi): **L\* 85.7 - C\*ab 8.7 - h 257.0deg**

Esikler: `dC*ab <= 2.0` - `dh <= 2.0deg` - `dL* <= 10` - `L* <= 92` - `doku orani >= 0.70`

| kare | L* | C*ab | h(deg) | dC | dh | dL | doku | kaplama | sonuc |
|---|---|---|---|---|---|---|---|---|---|
| 01_hero_fullbody | 68.9 | 8.9 | 271.1 | 0.19 | 14.08 | 16.8 | 0.70 | 9% | **FAIL** - hue dh=14.1deg, aciklik dL=16.8, doku kaybi 0.70 |
| 02_medium_collar | 72.3 | 9.7 | 268.0 | 1.03 | 11.00 | 13.4 | 0.69 | 22% | **FAIL** - hue dh=11.0deg, aciklik dL=13.4, doku kaybi 0.69 |
| 03_detail_texture | 69.2 | 9.6 | 270.9 | 0.87 | 13.91 | 16.5 | 0.86 | 72% | **FAIL** - hue dh=13.9deg, aciklik dL=16.5 |
| 04_back_view | 67.0 | 12.0 | 272.3 | 3.30 | 15.27 | 18.7 | 0.72 | 10% | **FAIL** - chroma dC=3.3, hue dh=15.3deg, aciklik dL=18.7 |
| 05_pdp_front | 78.9 | 7.4 | 270.3 | 1.28 | 13.32 | 6.8 | 0.63 | 9% | **FAIL** - hue dh=13.3deg, doku kaybi 0.63 |
| 06_pdp_three_quarter | 72.5 | 8.0 | 267.6 | 0.69 | 10.58 | 13.2 | 0.74 | 8% | **FAIL** - hue dh=10.6deg, aciklik dL=13.2 |
| 07_pdp_medium | 75.0 | 10.2 | 272.0 | 1.52 | 15.00 | 10.7 | 0.69 | 38% | **FAIL** - hue dh=15.0deg, aciklik dL=10.7, doku kaybi 0.69 |
| 08_detail_cuff | 81.1 | 9.6 | 273.5 | 0.87 | 16.49 | 4.6 | 0.94 | 30% | **FAIL** - hue dh=16.5deg |
| 09_social_candid | 72.0 | 8.2 | 270.1 | 0.50 | 13.05 | 13.7 | 0.73 | 25% | **FAIL** - hue dh=13.0deg, aciklik dL=13.7 |
| 10_social_vertical | 74.5 | 7.2 | 276.3 | 1.47 | 19.29 | 11.2 | 0.78 | 8% | **FAIL** - hue dh=19.3deg, aciklik dL=11.2 |

**Gecen: 0/10**

_Not: olcum kumas renginden turetilen maskeden aliniyor; arka plan, ten ve alt parca disarida. Kaplama = maskenin kare alanina orani, kumasin ne kadarinin olculdugunu gosterir. Segmentasyon (SAM3) ile maske daha da keskinlesir._