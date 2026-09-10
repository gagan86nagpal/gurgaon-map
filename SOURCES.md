# Source of truth for every price on the map

223 premium-project quotes (locality-average rows excluded). Each row in `agent_*.json` carries a `sot` field with the same information; the map shows the source label on every quote and links the page it was read from.

## Where the numbers come from

| Source | Quotes | Share | What the figure is |
|---|---:|---:|---|
| Square Yards | 202 | 90.6% | project page 'current asking price' — listing asks blended with registered-transaction data, updated quarterly |
| 99acres | 7 | 3.1% | listing-based project/locality average asking price |
| Business Standard | 3 | 1.3% | reported sale / developer-stated price |
| bigestate.io | 1 | 0.4% | broker/channel-partner quote — quoted unit price ÷ super area |
| Prestige Sector 92 project site | 1 | 0.4% | quoted unit price ÷ super area (project marketing site) |
| opulnzabode.com | 1 | 0.4% | broker/channel-partner quote — quoted unit price ÷ super area |
| superluxere.com | 1 | 0.4% | broker/channel-partner quote — quoted unit price ÷ super area |
| megarealtymax.com | 1 | 0.4% | broker/channel-partner quote — quoted unit price ÷ super area |
| ATS Grandstand project site | 1 | 0.4% | quoted unit price ÷ super area (project marketing site; not the atshomekraft.com corporate domain) |
| M3M (developer site) | 1 | 0.4% | developer's own published price |
| samagrarealty.in | 1 | 0.4% | broker/channel-partner quote — quoted unit price ÷ super area |
| MagicBricks | 1 | 0.4% | listing-based project average asking price |
| Housing.com | 1 | 0.4% | listing-based project average asking price |
| premiumrealtyinfra.com | 1 | 0.4% | broker/channel-partner quote — quoted unit price ÷ super area |

| Class | Quotes | Share |
|---|---:|---:|
| portal | 211 | 94.6% |
| broker | 6 | 2.7% |
| news | 3 | 1.3% |
| project-site | 2 | 0.9% |
| developer | 1 | 0.4% |

Rows with a second, independent source recorded: 23 (10.3%).
Confidence grades among audited rows: A 16, B 55, C 3.

## Caveats you should know

- Square Yards dominates because it is the only major portal whose project pages could be fetched programmatically during the build (99acres, MagicBricks and Housing block automated access). Its "current asking price" blends listing asks with government-registered transaction data, so it is usually closer to achieved prices than a pure listing average — but it is still one vendor's model.
- 99acres figures are pure listing averages (what sellers ask, not what buyers pay).
- Developer and project-site quotes are the developer's own asking price for a specific configuration (unit price ÷ super area). They are exact for that unit but represent the launch/primary market, not resale.
- Broker microsites are channel-partner pages; the arithmetic was verified but the price is whatever the broker chose to advertise.
- Audit notes and second-source links on individual quotes are in the map's inspector and in the `audit` / `second_source_url` fields.

## Every quote

| Sector | Project | ₹/sq ft | Source | Grade | As of | Link |
|---|---|---:|---|:-:|---|---|
| 3 | Sector 3 apartments incl. Godrej Habitat (resale) | 8,800–10,500 | 99acres | – | 2026-01 | [99acres.com](https://www.99acres.com/sector-3-gurgaon-overview-piffid) |
| 3A | Maa Bhagwati Residency, SS Residency Sector 3A, Shree Ganesh Apartment (resale) | 5,100–5,500 | Square Yards | A | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-3a-gurgaon) |
| 5 | Sector 5 villas/floors (resale) | 26,800 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-5-gurgaon) |
| 6 | WMG Tower Apartments (resale) | 8,350 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/property-rates/sector-6-gurgaon) |
| 8 | Ansal Eden Villa (resale) | 10,900 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-8-gurgaon) |
| 9 | R Infra Apartment / Huda HBC Society (resale) | 8,050–9,200 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/property-rates/sector-9-gurgaon) |
| 9A | Sector 9A apartments (resale) | 7,450–9,700 | Square Yards | C | 2026-09 | [squareyards.com](https://www.squareyards.com/sector-9a-in-gurgaon-overview-10) |
| 10A | Sector 10A flats (resale) | 7,500–10,950 | Square Yards | C | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-10a-gurgaon) |
| 12 | Raheja Qutab Farms / Platinum Greens (resale) | 11,100–11,200 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-12-gurgaon) |
| 12A | Stanford Amaara Residences | 8,000–8,400 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-12a-gurgaon) |
| 14 | ODR Residency (resale) | 15,550 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-14-gurgaon) |
| 14 | Old DLF Colony / Riddhi Siddhi Apartments (resale) | 22,200 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-14-gurgaon) |
| 15II | Anaheeta Homes Luxury Residential Apartments (Sector 15 Part 2, new launch) | 31,500 | 99acres | B | 2026-01 | [99acres.com](https://www.99acres.com/sector-15-part-2-gurgaon-overview-piffid) |
| 16 | TDI Palm Court (resale) | 15,250 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/property-rates/sector-16-gurgaon) |
| 17 | Sukh Residency (resale) | 15,600 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/property-rates/sector-17-gurgaon) |
| 22 | Alphacorp Gurgaon One 22 (resale) | 16,800 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-22-gurgaon) |
| 22 | Ambience Creacions (resale) | 21,400 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-22-gurgaon) |
| 22 | JMD The Park Way (resale) | 13,050 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-22-gurgaon) |
| 23 | Ansal Plaza Sector-23 (resale) | 15,500 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/property-rates/sector-23-gurgaon) |
| 24 | Ambience Caitriona | 20,600 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/ambience-caitriona/340/project) |
| 24 | Ambience Island Lagoon | 18,800 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/dlf-the-crest/343/project) |
| 24 | DLF Belvedere Towers | 19,200 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/dlf-the-crest/347/project) |
| 25 | Unitech Heritage City | 22,000 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/dlf-the-crest/366/project) |
| 26 | DLF Silver Oaks | 19,450 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/dlf-silver-oaks/361/project) |
| 27 | DLF Regency Park II | 21,500–22,150 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/dlf-regency-park-ii/354/project) |
| 28 | DLF Beverly Park I | 25,000 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/dlf-the-crest/348/project) |
| 28 | Silverglades The Ivy | 24,700–25,100 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/dlf-the-crest/330/project) |
| 30 | Unitech Uniworld City | 21,200 | Square Yards | A | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-30-gurgaon) |
| 31 | Birla Arika | 22,000–28,000 | Square Yards | B | 2026-01 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/birla-arika/325363/project) |
| 36A | Krisumi Waterfall Residences | 19,350 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/krisumi-waterfall-residences/10781/project) |
| 36A | Krisumi Waterfall Suites | 19,200–21,500 | Square Yards | – | 2025-Q4 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/krisumi-waterfall-suites/339846/project) |
| 36A | Krisumi Waterside Residences | 23,980–24,030 | Square Yards | A | 2026-09 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/krisumi-waterside-residences/247870/project) |
| 37D | BPTP The Amaario | 17,250 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-37d-gurgaon) |
| 37D | Ramprastha Primera | 10,000 | Square Yards | B | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-37d-gurgaon) |
| 37D | Signature Global De Luxe DXP | 16,500 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-37d-gurgaon) |
| 37D | Signature Global Sarvam | 15,950–16,000 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-37d-gurgaon) |
| 40 | Unitech Ivory Towers | 19,100 | Square Yards | B | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/unitech-ivory-towers/369/project) |
| 41 | South City 1 / South City Arcade (resale) | 16,650 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-41-gurgaon) |
| 41 | Unitech Rakshak (resale) | 9,500 | Square Yards | A | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-41-gurgaon) |
| 42 | DLF The Aralias | 45,000–58,000 | Square Yards | B | 2026-07 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/dlf-the-crest/328/project) |
| 42 | DLF The Camellias | 80,000–100,000 | Business Standard | A | 2026-06 | [business-standard.com](https://www.business-standard.com/finance/personal-finance/270-cr-in-30-days-dlf-camellias-in-gurgaon-is-india-s-most-elite-address-125110900102_1.html) |
| 42 | DLF The Magnolias | 70,200 | Square Yards | A | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/dlf-the-magnolias/333/project) |
| 43 | Craft Destination 43 (resale) | 22,150 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/property-rates/sector-43-gurgaon) |
| 43 | DLF Richmond Park | 26,100 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/dlf-the-crest/356/project) |
| 43 | DLF Richmond Park (resale) | 26,150 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/property-rates/sector-43-gurgaon) |
| 43 | DLF The Icon | 33,050 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/dlf-the-icon/314/project) |
| 43 | DLF The Pinnacle | 32,000 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/dlf-the-crest/370/project) |
| 45 | Ardee Platinum Greens (resale) | 13,400 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/property-rates/sector-45-gurgaon) |
| 45 | Unitech Greenwood City Apartment (resale) | 16,550 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/property-rates/sector-45-gurgaon) |
| 47 | Bestech Park View Spa | 14,170–18,750 | Square Yards | – | 2026-07 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/bestech-park-view-spa/295/project) |
| 48 | Central Park II-Bellevue | 16,750 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/central-park-ii-bellevue/303/project) |
| 48 | Central Park Resorts | 28,500–29,500 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/central-park-resorts/106940/project) |
| 48 | Experion The Trillion | 21,000–22,000 | Square Yards | A | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-48-gurgaon) |
| 49 | Elan The Statement | 23,650 | Square Yards | – | 2026-07 | [squareyards.com](https://www.squareyards.com/property-rates/sector-49-gurgaon) |
| 49 | Godrej Aristocrat | 20,950 | Square Yards | – | 2026-07 | [squareyards.com](https://www.squareyards.com/property-rates/sector-49-gurgaon) |
| 49 | Vatika City | 18,950 | Square Yards | – | 2026-07 | [squareyards.com](https://www.squareyards.com/property-rates/sector-49-gurgaon) |
| 50 | Elan Nirvana | 17,700 | Square Yards | – | 2026-07 | [squareyards.com](https://www.squareyards.com/property-rates/sector-50-gurgaon) |
| 50 | Unitech Fresco | 11,000–11,150 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/unitech-fresco/51/project) |
| 50 | Unitech Nirvana Country Aspen Greens | 18,800 | Square Yards | – | 2026-07 | [squareyards.com](https://www.squareyards.com/property-rates/sector-50-gurgaon) |
| 51 | Ocus Quantum | 15,000 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/property-rates/sector-51-gurgaon) |
| 51 | SS Mayfield Gardens | 13,450 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/property-rates/sector-51-gurgaon) |
| 53 | DLF Westend Heights | 28,400 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/dlf-the-crest/325/project) |
| 53 | Godrej Sora | 31,999 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/godrej-sora/340423/project) |
| 53 | Vipul Belmonte | 27,300 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/vipul-belmonte/401/project) |
| 54 | DLF Park Place | 34,500–37,000 | Square Yards | – | 2025-12 | [squareyards.com](https://www.squareyards.com/sale/resale-properties-in-dlf-park-place-gurgaon) |
| 54 | DLF The Belaire | 36,800–42,000 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/dlf-the-crest/338/project) |
| 54 | DLF The Crest | 54,100–60,000 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/dlf-the-aralias/332/project) |
| 54 | DLF The Dahlias | 100,000–160,000 | Business Standard | A | 2026-08 | [business-standard.com](https://www.business-standard.com/finance/personal-finance/271-crore-for-one-penthouse-dlf-s-the-dahlias-sets-new-luxury-benchmark-126081000587_1.html) |
| 54 | DLF The Summit | 35,400 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/dlf-beverly-park-ii/312/project) |
| 54 | Emaar The Palm Springs | 36,650 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/dlf-the-crest/320/project) |
| 54 | Salcon The Verandas | 36,100 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/salcon-the-verandas/327/project) |
| 56 | Trevoc Royal Residences | 25,900–26,100 | Square Yards | A | 2026-08 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/trevoc-royal-residences/308421/project) |
| 57 | BPTP Freedom Park Life (resale) | 14,500 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/property-rates/sector-57-gurgaon) |
| 57 | Suncity Sukriti CGHS Ltd (resale) | 15,000 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/property-rates/sector-57-gurgaon) |
| 57 | The Legend One (resale) | 15,900 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/property-rates/sector-57-gurgaon) |
| 58 | Ireo Grand Arch | 20,000–25,000 | 99acres | – | 2025-12 | [99acres.com](https://www.99acres.com/ireo-the-grand-arch-resale-in-sector-58-gurgaon-12210-npffid) |
| 59 | Max Estate 59 | 28,000–33,000 | opulnzabode.com | C | 2026-07 | [opulnzabode.com](https://www.opulnzabode.com/max-estate-59-sector-59-gcer-gurgaon-5000-5500-sqft-private-lift-lobby-2026/) |
| 60 | Ireo Skyon | 20,250–20,300 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/ireo-skyon/64/project) |
| 61 | Smartworld Orchard | 15,900–16,550 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/smart-world-orchard/103238/project) |
| 62 | Emaar Urban Oasis | 19,100–20,000 | Square Yards | B | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/emaar-urban-oasis/229603/project) |
| 62 | Pioneer Araya | 24,300–28,000 | Square Yards | B | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/pioneer-araya/21119/project) |
| 63 | Adani Samsara Vilasa | 18,800–19,500 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-63-gurgaon) |
| 63 | DLF The Arbour | 25,500–27,000 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-63-gurgaon) |
| 63A | Sobha Crescent | 25,000–31,850 | superluxere.com | – | 2026-03 | [superluxere.com](https://superluxere.com/blogs/sobha-crescent-sector-63a-gurgaon-price-list-payment-plan) |
| 65 | M3M Golf Estate | 25,000 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/m3m-golf-estate/68/project) |
| 65 | Trump Towers Delhi NCR (Tribeca) | 33,000–40,000 | megarealtymax.com | B | 2026-09 | [megarealtymax.com](https://megarealtymax.com/residential-property/trump-tower-sector-65-gurgaon) |
| 66 | Emaar MGF The Palm Drive Villas | 20,450–21,850 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/emaar-mgf-the-palm-drive-villas/20901/project) |
| 67 | M3M Merlin | 19,050–21,000 | Square Yards | B | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/m3m-merlin/61/project) |
| 68 | M3M Sierra | 12,500 | Square Yards | – | 2026-07 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/m3m-sierra/7396/project) |
| 69 | Smartworld Sky Arc | 21,300 | 99acres | – | 2026-07 | [99acres.com](https://www.99acres.com/property-rates-and-price-trends-in-sector-69-gurgaon-prffid) |
| 69 | Tulip Leaf | 16,850 | Square Yards | – | 2026-07 | [squareyards.com](https://www.squareyards.com/property-rates/sector-69-gurgaon) |
| 69 | Tulip Purple | 11,650 | 99acres | – | 2026-07 | [99acres.com](https://www.99acres.com/property-rates-and-price-trends-in-sector-69-gurgaon-prffid) |
| 69 | Unitech Sunbreeze | 9,500 | 99acres | – | 2026-07 | [99acres.com](https://www.99acres.com/property-rates-and-price-trends-in-sector-69-gurgaon-prffid) |
| 70 | Signature Global City (Sector 70) | 11,200–14,600 | samagrarealty.in | B | 2025-08 | [samagrarealty.in](https://samagrarealty.in/property/signature-global-city-sector-70-gurgaon/) |
| 70A | M3M Escala | 14,550 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/m3m-escala/384/project) |
| 71 | Signature Global Titanium SPR (SPR Estate) | 18,000–18,750 | premiumrealtyinfra.com | B | 2026-07 | [premiumrealtyinfra.com](https://premiumrealtyinfra.com/properties/signature-global-spr-estate) |
| 72 | Tata Primanti | 19,473 | MagicBricks | – | 2026-06 | [magicbricks.com](https://www.magicbricks.com/tata-primanti-sector-72-gurgaon-pdpid-4d4235303030313431) |
| 72 | Tata Primanti Phase 2 | 20,150 | Square Yards | – | 2026-07 | [squareyards.com](https://www.squareyards.com/property-rates/sector-72-gurgaon) |
| 72 | Tata Primanti-Tower Residences | 19,600 | Square Yards | – | 2026-07 | [squareyards.com](https://www.squareyards.com/property-rates/sector-72-gurgaon) |
| 72A | Birla Pravaah | 15,150–17,600 | Square Yards | – | 2026-07 | [squareyards.com](https://www.squareyards.com/sector-72a-in-gurgaon-overview-63959) |
| 73 | DLF Alameda | 15,300–15,800 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-73-gurgaon) |
| 74 | M3M Skywalk | 17,100–17,400 | Square Yards | – | 2026-03 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/m3m-skywalk/225841/project) |
| 76 | DLF Privana North | 23,500 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-76-gurgaon) |
| 76 | DLF Privana South | 17,150 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/dlf-privana-south/238058/project) |
| 76 | DLF Privana West | 22,400–24,500 | Square Yards | – | 2025-Q3 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/dlf-privana-west/247372/project) |
| 76 | Whiteland Blissville | 13,300 | Square Yards | – | 2026-07 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/whiteland-blissville/171090/project) |
| 76 | Whiteland The Aspen | 15,500–18,250 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/whiteland-the-aspen/215900/project) |
| 77 | Emaar Palm Heights | 13,500 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-77-gurgaon) |
| 77 | Emaar Palm Premier | 16,550 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-77-gurgaon) |
| 77 | Emaar Palm Select | 16,550 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-77-gurgaon) |
| 78 | Ganga Green Valley | 14,650 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-78-gurgaon) |
| 78 | Ganga Valley Floors | 14,416–14,550 | Housing.com | – | 2026-09 | [housing.com](https://housing.com/in/buy/projects/page/348520-ganga-valley-floors-by-ganga-realty-in-sector-78) |
| 78 | Mapsko Aspr Hills | 20,000 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-78-gurgaon) |
| 79 | Godrej Aria | 11,600 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-79-gurgaon) |
| 79 | Godrej Arista | 14,950 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-79-gurgaon) |
| 79 | M3M Antalya Hills | 14,750 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-79-gurgaon) |
| 79 | M3M Golf Hills | 14,050–15,100 | Square Yards | – | 2025-Q3 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/m3m-golf-hills/220071/project) |
| 79B | Signature Global City 79B | 12,100 | Square Yards | – | 2026-07 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/signature-global-city-79b/216718/project) |
| 80 | Eldeco Fairway Reserve | 17,500 | Square Yards | – | 2026-07 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/eldeco-fairway-reserve/324073/project) |
| 80 | Godrej Frontier | 10,400–10,550 | Square Yards | A | 2026-07 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/godrej-frontier/125/project) |
| 80 | Sobha Aranya | 23,900–25,000 | Square Yards | – | 2026-07 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/sobha-aranya/247019/project) |
| 81 | Bestech Park View Grand Spa | 13,200–13,400 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-81-gurgaon) |
| 81 | DLF The Ultima | 17,700 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-81-gurgaon) |
| 81 | DLF Ultima Phase II | 17,300–17,900 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-81-gurgaon) |
| 82 | Mapsko Casa Bella - Villas | 10,400 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-82-gurgaon) |
| 82 | Vatika India Next | 12,500–12,900 | Square Yards | – | 2026-Q1 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/vatika-india-next/5268/project) |
| 82 | Vatika Seven Lamps | 11,300 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-82-gurgaon) |
| 82A | Vatika Town Square | 16,650–16,750 | Square Yards | B | 2026-07 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/vatika-town-square/144139/project) |
| 83 | Emaar Palm Gardens | 13,550 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-83-gurgaon) |
| 83 | Vatika Boulevard Heights and Residences | 8,400 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/vatika-boulevard-heights-and-residences/100111/project) |
| 83 | Vatika Gurgaon 21 | 10,950 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-83-gurgaon) |
| 84 | Ganga Nandaka | 8,550–11,300 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/sector-84-in-gurgaon-overview-103) |
| 84 | Signature Global Twin Tower DXP | 8,550–11,300 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/sector-84-in-gurgaon-overview-103) |
| 85 | Ganga Anantam | 14,000–14,800 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-85-gurgaon) |
| 85 | Godrej Air | 12,900–13,700 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-85-gurgaon) |
| 85 | Orris Aster Court Premier | 11,500–11,900 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-85-gurgaon) |
| 86 | DLF New Town Heights II | 11,000 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-86-gurgaon) |
| 86 | DLF The Skycourt | 12,400 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-86-gurgaon) |
| 86 | Emaar Serenity Hills | 17,250 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-86-gurgaon) |
| 87 | Anant Raj Maceo | 10,850 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-87-gurgaon) |
| 87 | DLF New Town Heights II | 11,000 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-87-gurgaon) |
| 87 | DLF The Skycourt | 12,400 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-87-gurgaon) |
| 88A | Godrej Icon | 13,500 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-88a-gurgaon) |
| 88A | Godrej Oasis | 11,650 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-88a-gurgaon) |
| 88A | Signature Global Imperial | 15,350 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-88a-gurgaon) |
| 88B | Trinity Sky Palazzo | 17,500 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/trinity-sky-palazzo/325651/project) |
| 88B | Vatika One Express City | 12,900 | Square Yards | A | 2026-09 | [squareyards.com](https://www.squareyards.com/sector-88b-in-gurgaon-overview-109) |
| 89 | M3M Soulitude | 10,900–13,000 | Square Yards | B | 2025-12 | [squareyards.com](https://www.squareyards.com/blog/m3m-soulitude-price-list) |
| 89A | ATS Marigold | 12,900 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-89a-gurgaon) |
| 89A | Adani Aangan | 11,450 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-89a-gurgaon) |
| 89A | Vatika Seven Elements | 12,500 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-89a-gurgaon) |
| 90 | DLF New Town Heights I | 10,750–10,850 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-90-gurgaon) |
| 90 | DLF Regal Gardens | 7,100–7,200 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-90-gurgaon) |
| 90 | SS Camasa | 13,500–15,000 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-90-gurgaon) |
| 91 | Anant Raj Maceo (now marketed as TARC Maceo) | 10,600–10,850 | Square Yards | B | 2026-08 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/anant-raj-maceo/153/project) |
| 92 | Bestech Park View Sanskruti | 11,900–12,100 | 99acres | – | 2026-06 | [99acres.com](https://www.99acres.com/bestech-park-view-sanskruti-sector-92-gurgaon-npxid-r4600) |
| 92 | Prestige City / Prestige Sector 92 | 12,700–13,100 | Prestige Sector 92 project site | B | 2026-09 | [prestigesector92gurgaon.com](https://prestigesector92gurgaon.com/) |
| 92 | Signature Global City 92 | 13,000 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-92-gurgaon) |
| 93 | Ashiana Amarah | 14,350 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-93-gurgaon) |
| 93 | Ashiana Amarah (Phase 4 sales data) | 13,000–14,200 | Business Standard | – | 2026-09 | [business-standard.com](https://www.business-standard.com/companies/news/ashiana-housing-sells-properties-worth-rs-403-49-cr-in-gurugram-project-124090400639_1.html) |
| 93 | DLF Gardencity Enclave | 12,450 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-93-gurgaon) |
| 93 | Signature Global City 93 | 12,200 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-93-gurgaon) |
| 94 | DLF Gardencity Enclave | 12,450 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-94-gurgaon) |
| 94 | Orris Aanandam Ora | 13,550 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-94-gurgaon) |
| 95 | Signature Global Aspire | 10,250 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-95-gurgaon) |
| 95 | Signature Global Superbia | 10,000 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-95-gurgaon) |
| 95A | Signature Global The Roselia | 8,700 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-95a-gurgaon) |
| 95A | Signature Roselia Phase 2 | 10,150 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sector-95a-gurgaon) |
| 99 | Vatika Sovereign Park | 13,650–13,900 | bigestate.io | – | 2026-09 | [bigestate.io](https://www.bigestate.io/in/gurgaon/sector-99) |
| 99A | ATS HomeKraft Grandstand Phase 2 | 14,824–14,967 | ATS Grandstand project site | B | 2026-09 | [atsgrandstandgurgaon.in](https://atsgrandstandgurgaon.in/index.html) |
| 99A | ATS Tangerine | 6,000 | Square Yards | A | 2026-09 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/ats-tangerine/1157/project) |
| 99A | Conscient Habitat Prime | 8,300–10,850 | Square Yards | – | 2025-11 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/conscient-habitat-prime/113865/project) |
| 100 | BPTP The Amaario | 17,250 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-100-gurgaon) |
| 100 | Conscient Heritage Max | 13,850 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-100-gurgaon) |
| 100 | Vatika Sovereign Park | 13,900 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-100-gurgaon) |
| 102 | BPTP Amstoria Verti Greens | 17,450–21,000 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/bptp-amstoria-verti-greens/325205/project) |
| 102 | BPTP GAIA Residences | 21,000 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-102-gurgaon) |
| 102 | Emaar Gurgaon Greens | 11,758–12,424 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/emaar-gurgaon-greens/245/project) |
| 102 | Shapoorji Pallonji Joyville Phase 3 | 15,500–17,200 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/shapoorji-pallonji-joyville-phase-3/102367/project) |
| 102A | Adani The Marq | 17,000 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-102a-gurgaon) |
| 103 | Godrej Vrikshya | 19,697–19,713 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/godrej-vrikshya/251902/project) |
| 103 | Whiteland Urban Resort | 25,700–26,800 | Square Yards | A | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/whiteland-urban-resort/250439/project) |
| 104 | ATS Triumph | 12,950 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-104-gurgaon) |
| 104 | Central Park Delphine | 28,000–30,000 | Square Yards | A | 2026-09 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/delphine-central-park-estates/341264/project) |
| 104 | Godrej Premia Tower / Signature Homes | 16,100–16,250 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-104-gurgaon) |
| 104 | Hero Homes Palatial | 18,500 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-104-gurgaon) |
| 105 | ATS Homekraft Sanctuary | 14,000 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-105-gurgaon) |
| 106 | Elan The Presidential | 18,100–22,750 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/elan-the-presidential/205270/project) |
| 106 | Godrej Meridien | 15,520–17,280 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/godrej-meridien/10157/project) |
| 106 | Sobha Altus | 21,000–23,500 | Square Yards | – | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/sobha-altus/249540/project) |
| 107 | M3M Woodshire | 9,650 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-107-gurgaon) |
| 108 | Experion The Heart Song | 11,800–12,400 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/property-rates/sector-108-gurgaon) |
| 108 | Experion The Westerlies | 10,500–13,450 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/experion-the-westerlies/352/project) |
| 108 | Sobha City | 20,650–21,050 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/sobha-city-gurgaon/8365/project) |
| 109 | ATS Kocoon | 13,300 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-109-gurgaon) |
| 109 | ATS Tourmaline | 13,050 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-109-gurgaon) |
| 109 | Conscient One (Service Apartments) | 14,300 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-109-gurgaon) |
| 109 | Sobha International City | 13,300–17,000 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-109-gurgaon) |
| 110 | Indiabulls Enigma | 14,200 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-110-gurgaon) |
| 110A | Mahindra Aura | 13,500–14,300 | Square Yards | B | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/mahindra-aura/272/project) |
| 111 | M3M Crown | 16,400–21,900 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-111-gurgaon) |
| 111 | M3M Elie Saab | 33,000–35,000 | Square Yards | A | 2026-06 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/m3m-elie-saab/341930/project) |
| 111 | Puri Diplomatic Greens Phase I | 16,150–17,100 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-111-gurgaon) |
| 111 | Puri Diplomatic Residences | 19,000 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-111-gurgaon) |
| 112 | Emaar The 88 | 15,500–15,520 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-112-gurgaon) |
| 112 | Emaar Urban Ascent | 17,490–17,510 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-112-gurgaon) |
| 112 | Experion Windchants | 14,500–15,860 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-112-gurgaon) |
| 112 | Tata Gurgaon Gateway | 13,770–13,780 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/projects-in-sector-112-gurgaon) |
| 113 | M3M Capital | 16,990–17,025 | Square Yards | – | 2026-09 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/m3m-capital/117500/project) |
| 113 | M3M Mansion | 22,000–24,000 | Square Yards | B | 2026-09 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/m3m-mansion/246483/project) |
| 113 | Smartworld One DXP | 19,500–21,000 | Square Yards | A | 2026-09 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/smart-world-one-dxp/210648/project) |
| Manesar | M3M Gurgaon International City | 11,000–13,500 | M3M (developer site) | – | 2025-11 | [m3mproperties.com](https://www.m3mproperties.com/residential/gurugram/m3m-manesar/) |
| Sohna-2 | Ashiana Mulberry | 11,050 | Square Yards | – | 2026-07 | [squareyards.com](https://www.squareyards.com/property-rates/sohna-sector-2-gurgaon) |
| Sohna-2 | Eldeco Accolade | 10,550 | Square Yards | – | 2026-07 | [squareyards.com](https://www.squareyards.com/property-rates/sohna-sector-2-gurgaon) |
| Sohna-5 | Ganga Tathastu | 9,750 | Square Yards | – | 2026-07 | [squareyards.com](https://www.squareyards.com/property-rates/sohna-sector-5-gurgaon) |
| Sohna-33 | Ashiana Anmol | 11,000–11,250 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sohna-sector-33-gurgaon) |
| Sohna-33 | Central Park Flower Valley | 13,600 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sohna-sector-33-gurgaon) |
| Sohna-33 | Godrej Nature Plus | 12,000 | Square Yards | – | 2026-08 | [squareyards.com](https://www.squareyards.com/projects-in-sohna-sector-33-gurgaon) |
| Sohna-33 | Godrej Serenity | 12,000 | Square Yards | – | 2026-07 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/godrej-serenity-gurgaon/103189/project) |
| Sohna-35 | ATS Homekraft Bonheur Avenue | 11,250 | Square Yards | – | 2026-07 | [squareyards.com](https://www.squareyards.com/property-rates/sohna-sector-35-gurgaon) |
| Sohna-35 | Silverglades The Melia | 9,250 | Square Yards | – | 2026-07 | [squareyards.com](https://www.squareyards.com/property-rates/sohna-sector-35-gurgaon) |
| Sohna-36 | Krisumi Waterfall Residences | 19,350 | Square Yards | – | 2026-07 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/krisumi-waterfall-residences/10781/project) |
| Sohna-36 | Signature Global Park | 9,800–10,200 | Square Yards | – | 2026-Q1 | [squareyards.com](https://www.squareyards.com/gurgaon-residential-property/signature-global-park/10718/project) |
