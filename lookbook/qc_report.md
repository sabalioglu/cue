# QC raporu - Attir waffle polo lookbook

Referans (urun fotografi): **L\* 83.6 - C\*ab 26.5 - h 98.4deg**

Esikler: `dC*ab <= 2.0` - `dh <= 2.0deg` - `dL* <= 10` - `L* <= 92` - `doku orani >= 0.70`

| kare | L* | C*ab | h(deg) | dC | dh | dL | doku | sonuc |
|---|---|---|---|---|---|---|---|---|
| 01_hero_fullbody | 81.5 | 18.0 | 104.9 | 8.56 | 6.48 | 2.1 | 0.67 | **FAIL** - chroma dC=8.6, hue dh=6.5deg, doku kaybi 0.67 |
| 02_medium_wall | 78.7 | 22.0 | 93.4 | 4.54 | 4.94 | 5.0 | 0.84 | **FAIL** - chroma dC=4.5, hue dh=4.9deg |
| 03_detail_texture | 83.9 | 32.1 | 95.0 | 5.55 | 3.34 | 0.3 | 1.04 | **FAIL** - chroma dC=5.6, hue dh=3.3deg |
| 04_back_view | 78.2 | 22.4 | 94.7 | 4.10 | 3.68 | 5.4 | 0.66 | **FAIL** - chroma dC=4.1, hue dh=3.7deg, doku kaybi 0.66 |
| 05_pdp_front | 78.7 | 19.3 | 93.0 | 7.21 | 5.41 | 4.9 | 0.74 | **FAIL** - chroma dC=7.2, hue dh=5.4deg |
| 06_pdp_three_quarter | 80.0 | 15.9 | 94.6 | 10.66 | 3.83 | 3.6 | 0.69 | **FAIL** - chroma dC=10.7, hue dh=3.8deg, doku kaybi 0.69 |
| 07_pdp_medium | 82.6 | 25.5 | 93.5 | 1.01 | 4.90 | 1.0 | 0.95 | **FAIL** - hue dh=4.9deg |
| 08_detail_finish | 77.9 | 29.5 | 93.8 | 2.98 | 4.57 | 5.7 | 0.99 | **FAIL** - chroma dC=3.0, hue dh=4.6deg |
| 09_social_candid | 84.4 | 24.3 | 94.0 | 2.23 | 4.39 | 0.8 | 0.89 | **FAIL** - chroma dC=2.2, hue dh=4.4deg |
| 10_social_vertical | 84.4 | 20.0 | 93.8 | 6.48 | 4.55 | 0.8 | 0.65 | **FAIL** - chroma dC=6.5, hue dh=4.6deg, doku kaybi 0.65 |

**Gecen: 0/10**

_Not: olcum karenin merkez kutusundan aliniyor. Segmentasyon (SAM3) eklendiginde sadece kumas bolgesi olculerek dogruluk artar._