"""
Bruton x 2020 Bulkers - RTO dilution-kalkulator
================================================
Oppdatert 2026-08-16 mot PROSJEKTMAPPEN (fronten), ikke bare wikien.

PRIMAERKILDE FOR NAV-BENET:
  "2020 and Bruton RTO Hypothesis/Verdivurdering-Nye-Bruton-aug2026.docx"
  (verdsettelsesdato 13. august 2026, oppdaterer 10. juli-versjonen med
  H1 2026-rapporten). Wikiens rto-verdsettelse.md er fortsatt synket mot
  JULI-versjonen og er derfor utdatert pa flere punkter.
  Skallbenet bruker Verdivurdering-2020B-skall-jul2026.docx (ingen
  august-oppdatering finnes).

DEFAULTVERDIENE REPRODUSERER FRONTENS EGEN NAV-TABELL:
  Skips-EK $174,1M + kontanter $45M + charterverdi $8M = $227M
  -> NOK 2,16 mrd @ 9,49 -> NOK 35/aksje.  Triangulering NOK 1,9-2,7 mrd.

HVA SOM ER RETTET FRA FORRIGE APP-VERSJON:

1. FISJONEN ER STRUKTUR, IKKE EN JUSTERT PARAMETER.  Dilution regnes mot
   rest-Bruton (4 VLCC). OMC Tankers har eget ben, siden en Bruton-eier
   sitter med begge papirene og posisjonsverdien ellers blir feil.

2. LTV-BASEN.  Forrige versjon regnet EK som resale x (1 - LTV). SLB-en er
   90 % av KONTRAKTSPRIS. Med resale 175 og LTV 65 % ga gammel formel $61M
   pa Mount Vision; fronten har $49,3M. Feilen spiste opp nettopp den
   innebygde gevinsten som er hele saken.

3. KONTRAKTSPRISER OG GJENSTAENDE INSTALMENTS ER NA H1-BEKREFTEDE TALL
   (134,1 / 134,6 / 116,7 / 116,7; gjenstar 0 / 94,4 / 105,0 / 105,0),
   ikke estimater. Kilde: FS 30.06.2026, via frontens tabell 2 og 3.

4. TO NAV-METODER, IKKE EN.  Se METODEVALG under - forskjellen er ett
   tall, og den er verdt a se.

5. SLOT-PREMIEN VAR 0.  Kontraktene er 2023-priser mot dagens resale.
   A sette premien til null var a nulle ut tesen.

METODEVALG - hvorfor appen har en bryter her:
   Fronten verdsetter ALLE fire skip som "MV - 90 % av kontraktskost",
   ogsa de uleverte. Det tar ikke med at SLB-trekket ved levering er
   STORRE enn den gjenstaende terminen, slik at det frigjores kontanter.
   Mekanikken er bekreftet observert: Mount Vision utloste USD 40m
   tilbakebetalt i juli (H1-rapporten). Mount Horizon utloser tilsvarende
   ~USD 26,7m i november (0,90 x 134,6 - 94,4). Frontier/Summit utloser
   ~0, fordi 90 % av kostnaden akkurat dekker terminen deres.
   Forskjellen mellom metodene er derfor NOYAKTIG Horizons refusjon.
   Fronten er den konservative. Begge er tilgjengelige i appen.

IKKE INVESTERINGSRAD.
"""

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Bruton / 2020B RTO Dilution", page_icon="🚢", layout="wide")

# ---------------------------------------------------------------------------
# Konstanter
# ---------------------------------------------------------------------------
SHELL_CASH_USD_M = 4.0
SHARES_PRE_CANCEL_M = 22.93
SHARES_POST_CANCEL_M = 20.14
BRUT_SHARES_M = 61.9238      # H1 FS note 12: 61 923 808 (bekreftet)
SLB_ADVANCE = 0.90           # Vision 90 %; 85-90 % avhengig av kontraktslengde

# Rest-Bruton. kontrakt/gjenstar er H1-bekreftet; MV-band fra frontens tabell 4.
REST_FLEET = [
    # navn,            kontrakt, gjenstar, mv_lav, mv_mid, mv_hoy, levert
    ("Mount Vision",   134.1,   0.0,  165.0, 170.0, 175.0, True),
    ("Mount Horizon",  134.6,  94.4,  150.0, 160.0, 168.0, False),
    ("Mount Frontier", 116.7, 105.0,  140.0, 148.0, 155.0, False),
    ("Mount Summit",   116.7, 105.0,  140.0, 148.0, 155.0, False),
]

# OMC Tankers. Innbetalt er wiki-dokumentert fra primaerkilder - se KONFLIKT under.
OMC_FLEET = [
    ("Mount Vanguard",  124.75, 37.425, "CIMC Raffles", "jan 2028"),
    ("Mount Pursuit",   124.75, 37.425, "CIMC Raffles", "mar 2028"),
    ("Mount Pinnacle",  124.75, 37.425, "CIMC Raffles", "mai 2028"),
    ("Mount Discovery", 124.75, 37.425, "CIMC Raffles", "jul 2028"),
    ("Mount Endeavour", 118.00, 11.800, "New Times",    "des 2028"),
    ("Mount Odyssey",   118.00, 11.800, "New Times",    "mar 2029"),
    ("Mount Venture",   118.00, 11.800, "New Times",    "jul 2029"),
    ("Mount Voyager",   118.00, 11.800, "New Times",    "okt 2029"),
]
OMC_PAID_FRONT = 97.0        # frontens tall for samlet innbetalt i OMC
OMC_UNCOVERED_FRONT = 1062.0  # frontens tall for udekket program

SCENARIER = {
    "Lav":  {"mv": 3, "kontanter": 30.0, "charter": 0.0},
    "Mid":  {"mv": 4, "kontanter": 45.0, "charter": 8.0},
    "Høy":  {"mv": 5, "kontanter": 60.0, "charter": 15.0},
}


def verdi_levert(mv: float, kontrakt: float) -> float:
    """Levert skip: markedsverdi minus trukket SLB (90 % av KONTRAKTSPRIS)."""
    return mv - SLB_ADVANCE * kontrakt


def verdi_nybygg_front(mv: float, kontrakt: float) -> float:
    """Frontens metode: behandler nybygget som om gjelden alt er trukket."""
    return mv - SLB_ADVANCE * kontrakt


def verdi_nybygg_med_refusjon(mv: float, gjenstar: float) -> float:
    """Inkl. SLB-refusjon ved levering.

    Ved levering betales gjenstaende R og det trekkes D = 0,90 x kontrakt.
    Du eier et skip verdt MV, skylder D, og mottar netto (D - R) kontant:

        (MV - D) + (D - R)  =  MV - R

    D faller ut. Belaningsgraden pavirker ALTSA IKKE substansverdien -
    bare om transaksjonen lar seg gjennomfore. Derfor star det ingen
    LTV-input her, og derfor er OMCs manglende finansiering en RISIKO,
    ikke et NAV-fradrag.
    """
    return mv - gjenstar


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("Bruton × 2020 Bulkers — RTO dilution-kalkulator")
st.caption(
    "Oppdatert **16. august 2026**. NAV-benet er kalibrert mot "
    "`Verdivurdering-Nye-Bruton-aug2026.docx` (13. aug, H1-oppdatert). "
    "Skallet: spesialutbytte US$13,8/aksje = NOK 129,5 (16. april 2026), ~US$4M beholdt."
)

st.warning(
    "**Fisjonen er ikke gjennomført.** Betinget av *«a completed stock exchange listing "
    "of the shares in OMC Tankers Ltd.»*. Opptak **søkt, ikke innvilget** (14. aug, "
    "melding 679850). **Fisjonens bytteforhold er ikke publisert** — appen antar 1:1 i "
    "begge papirer. Rest-Brutons kurs eksisterer ikke ennå; den må estimeres til "
    "prisdannelsen har skjedd i to papirer. Svensen (Finansavisen 13. aug): splitt "
    "«senere denne måneden», flytting til Hovedliste/Expand «slutten av september eller "
    "begynnelsen av oktober», månedlige utbytter fra september.",
    icon="⚠️",
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Din posisjon")
    st.markdown("**Bruton (BRUT) — før fisjon**")
    my_brut = st.number_input("BRUT-aksjer", min_value=0, max_value=10_000_000,
                              value=1_000, step=100, key="brut_qty")
    my_brut_cost = st.number_input("GAV BRUT (NOK)", min_value=0.0, max_value=200.0,
                                   value=50.0, step=0.5)
    st.caption("Blir til aksjer i **både** rest-Bruton og OMC Tankers etter fisjonen.")

    st.markdown("---")
    st.markdown("**2020 Bulkers (2020B) — skall post-utbytte**")
    my_2020b = st.number_input("2020B-aksjer", min_value=0, max_value=10_000_000,
                               value=1_000, step=100, key="b20_qty")
    my_2020b_cost = st.number_input(
        "GAV 2020B post-utbytte (NOK)", min_value=0.0, max_value=20.0, value=2.5, step=0.1,
        help="Kjøpskurs ETTER at NOK 129,5 utbytte er trukket fra.",
    )

    st.markdown("---")
    st.header("Felles forutsetninger")
    scenario = st.radio(
        "Verdiscenario", list(SCENARIER.keys()), index=1, horizontal=True,
        help="Setter skipsverdier, kontantanker og charterverdi samtidig — "
             "reproduserer frontens tre NAV-kolonner (lav/mid/høy).",
    )
    usdnok = st.number_input(
        "USD/NOK", min_value=8.0, max_value=12.0, value=9.49, step=0.01,
        help="9,49 per 13. august 2026 (frontens kurs). Juli-versjonen brukte 9,80 — "
             "sterkere krone trakk konklusjonen ~3 % ned i NOK.",
    )
    nav_metode = st.radio(
        "NAV-metode for nybygg",
        ["Frontens (MV − 90 % kost)", "Inkl. SLB-refusjon ved levering"],
        index=0,
        help="Se modulen under for hva forskjellen består i. Frontens er den "
             "konservative; forskjellen er nøyaktig Mount Horizons refusjon.",
    )
    bruk_refusjon = nav_metode.startswith("Inkl.")
    st.caption("GAV = gjennomsnittlig anskaffelseskurs. La felt stå på 0 for grupper du ikke eier.")

sc = SCENARIER[scenario]
shell_cash_nok_m = SHELL_CASH_USD_M * usdnok

# ---------------------------------------------------------------------------
# NAV 1: rest-Bruton
# ---------------------------------------------------------------------------
with st.expander("📊 Rest-Bruton (Company A, 4 VLCC) — NAV-modell", expanded=True):
    st.markdown(
        "De fire første New Times-skrogene. Alle dekket av **sale-leaseback fra kinesisk "
        "leasinghus** (85–90 % av byggekost, Vision 90 %, 15 år, ~5,6 % fast bareboat, "
        "kjøpsopsjoner). Kontraktspriser og gjenstående instalments er **H1-bekreftede**, "
        "ikke estimater. Kontant-breakeven ~$39k/dag (DF LNG) / ~$35k/dag (konvensjonell); "
        "Svensen oppgir snitt **$37k/dag** over de fire."
    )

    rows_in = []
    for navn, kontrakt, gjenstar, lav, mid, hoy, levert in REST_FLEET:
        rows_in.append({
            "Skip": navn, "Kontrakt ($M)": kontrakt, "Gjenstår ($M)": gjenstar,
            "Markedsverdi ($M)": (lav, mid, hoy)[sc["mv"] - 3], "Levert": levert,
        })

    fleet = st.data_editor(
        pd.DataFrame(rows_in), hide_index=True, width="stretch",
        key=f"rest_editor_{scenario}",
        column_config={
            "Kontrakt ($M)": st.column_config.NumberColumn(
                format="%.1f", min_value=50.0, max_value=250.0,
                help="H1 2026 FS: 134,1 / 134,6 / 116,7 / 116,7, sum 502,0."),
            "Gjenstår ($M)": st.column_config.NumberColumn(
                format="%.1f", min_value=0.0, max_value=250.0,
                help="H1-bekreftet: 0 / 94,4 / 105,0 / 105,0. Innbetalt = kontrakt − gjenstår."),
            "Markedsverdi ($M)": st.column_config.NumberColumn(
                format="%.1f", min_value=80.0, max_value=280.0,
                help="Resale-komparabler, moderne prompt tonnasje ~$168–172M medio 2026, "
                     "fratrukket leveringstidspunkt, påslag for DF-spesifikasjon. "
                     "NB: Svensen oppgir at et stort meglerhus verdsetter samme type skip "
                     "på vannet til >$180M — over båndet som brukes her, så midtpunktet "
                     "er konservativt."),
        },
    )

    vis_rows, ship_eq, refusjon_sum = [], 0.0, 0.0
    for _, r in fleet.iterrows():
        mv, k, g = r["Markedsverdi ($M)"], r["Kontrakt ($M)"], r["Gjenstår ($M)"]
        refusjon = max(0.0, SLB_ADVANCE * k - g) if not r["Levert"] else 0.0
        refusjon_sum += refusjon
        if r["Levert"]:
            v, metode = verdi_levert(mv, k), "MV − 90 % × kontrakt"
        elif bruk_refusjon:
            v, metode = verdi_nybygg_med_refusjon(mv, g), "MV − gjenstår"
        else:
            v, metode = verdi_nybygg_front(mv, k), "MV − 90 % × kontrakt"
        ship_eq += v
        vis_rows.append({
            "Skip": r["Skip"],
            "Status": "Levert" if r["Levert"] else "Under bygging",
            "Innbetalt ($M)": f"{k - g:.1f}",
            "Slot-premie ($M)": f"{mv - k:+.1f}",
            "SLB-refusjon v/lev. ($M)": f"{refusjon:.1f}" if refusjon else "—",
            "Metode": metode,
            "Verdi ($M)": f"{v:.1f}",
        })

    st.dataframe(pd.DataFrame(vis_rows), hide_index=True, width="stretch")

    if not bruk_refusjon and refusjon_sum > 0.5:
        st.info(
            f"**Frontens metode utelater ${refusjon_sum:.1f}M i SLB-refusjon** som utløses "
            f"når Mount Horizon leveres i november: 0,90 × 134,6 − 94,4 = 26,7. "
            f"Mekanikken er ikke hypotetisk — den er observert: Mount Vision utløste "
            f"**$40M tilbakebetalt i juli**, bekreftet i H1-rapporten, og det beløpet "
            f"ligger i kontantankeret under. Frontier og Summit utløser ~0 fordi 90 % av "
            f"kostnaden akkurat dekker terminen deres. Bytt metode i sidepanelet for å se "
            f"effekten. **Åpent spørsmål til fronten:** er utelatelsen bevisst konservatisme, "
            f"eller ligger Horizons refusjon implisitt i kontantbåndet $30–60M?",
            icon="💡",
        )

    c1, c2 = st.columns(2)
    with c1:
        net_cash = st.number_input(
            "Netto kontanter ($M)", min_value=-100.0, max_value=200.0,
            value=sc["kontanter"], step=1.0, key=f"cash_{scenario}",
            help="Frontens bånd $30–60M, midtpunkt $45M — nå med observasjonsstøtte: "
                 "$11,8M per 30.06 + $40M SLB-refusjon mottatt i juli = $51,8M FØR "
                 "fisjonssplitt, noteringskostnader og OMCs 2026-instalments (~$23M på "
                 "2029-skipene). Trekker du de $23M fra, står ~$28,8M igjen å dele — "
                 "det peker mot nedre del av båndet, ikke midtpunktet.",
        )
    with c2:
        charter_val = st.number_input(
            "Charterverdi vs. midtsyklus ($M)", min_value=-20.0, max_value=60.0,
            value=sc["charter"], step=1.0, key=f"charter_{scenario}",
            help="Merverdi av at Vision ($95k/d, 9 mnd fast) og Horizon ($105,7k/d, "
                 "12–15 mnd) er fikset over midtsyklusnivå. Frontens bånd 0 / 8 / 15.",
        )

    nav_usd = ship_eq + net_cash + charter_val
    nav_nok = nav_usd * usdnok
    nav_ps = nav_nok / BRUT_SHARES_M

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Skips-egenkapital", f"${ship_eq:.1f}M",
              help="Fronten (mid, uten refusjon): $174,2M")
    k2.metric("NAV", f"${nav_usd:.0f}M", help="Fronten (mid): $227M")
    k3.metric("NAV i NOK", f"{nav_nok:,.0f} M".replace(",", " "),
              help="Fronten (mid): 2,16 mrd")
    k4.metric("NAV per aksje", f"{nav_ps:.1f} NOK", help="Fronten (mid): 35 NOK")

    st.caption(
        "**Frontens triangulering (13. aug):** NAV 1,6–2,6 mrd · DDM 2,0–2,9 mrd · "
        "peers 0,85–1,00 × NAV = 1,4–2,6 mrd → **konklusjon NOK 1,9–2,7 mrd "
        "(31–43 kr/aksje), midtpunkt ~2,2 mrd (~35 kr)**. "
        "⚠️ ±10 % på skipsverdier flytter NAV ~±35–40 % under 85–90 % giring. "
        "Resale-premien over nybygg (~$40M) er historisk anomal og er hovedrisikoen "
        "på nedsiden; normalisering av Hormuz-løftede rater er basisforutsetningen."
    )

# ---------------------------------------------------------------------------
# NAV 2: OMC
# ---------------------------------------------------------------------------
with st.expander("🏗️ OMC Tankers (Company B, 8 skrog) — NAV-modell", expanded=False):
    st.markdown(
        "Skrogene overføres til **nybyggingspris** (snitt $121,5M per Svensen), ikke til "
        "verdien på vannet — hele asset-play-spreaden blir liggende i OMC. Ingen kontanter, "
        "garantier eller krysseierskap mellom selskapene. **Ingen SLB er avtalt for disse "
        "åtte**, så «MV − 90 % kost» er ikke anvendelig; her gjelder innbetalt + slot-premie."
    )

    o1, o2 = st.columns(2)
    with o1:
        prem_cimc = st.number_input("Slot-premie per CIMC-skrog ($M)", min_value=-20.0,
                                    max_value=60.0, value=8.0, step=1.0,
                                    help="Levering jan–jul 2028. Kontrakt $124,75M. "
                                         "CIMC Raffles er førstegangsbygger av VLCC — "
                                         "forsinkelsesrisikoen går motsatt vei av New Times.")
    with o2:
        prem_nts = st.number_input("Slot-premie per NTS-skrog ($M)", min_value=-20.0,
                                   max_value=60.0, value=12.0, step=1.0,
                                   help="Levering des 2028 – okt 2029. Kontrakt $118M mot "
                                        "Svensens estimat på ~$130M for tilsvarende "
                                        "2029-levering bestilt i dag → ~$12M premie.")

    omc_rows, omc_val, omc_paid, omc_rem = [], 0.0, 0.0, 0.0
    for navn, kontrakt, innbetalt, verft, lev in OMC_FLEET:
        prem = prem_cimc if verft == "CIMC Raffles" else prem_nts
        v = innbetalt + prem
        omc_val += v
        omc_paid += innbetalt
        omc_rem += kontrakt - innbetalt
        omc_rows.append({
            "Skip": navn, "Verft": verft, "Levering": lev,
            "Kontrakt ($M)": f"{kontrakt:.2f}", "Innbetalt ($M)": f"{innbetalt:.1f}",
            "Slot-premie ($M)": f"{prem:+.1f}", "Verdi ($M)": f"{v:.1f}",
        })
    st.dataframe(pd.DataFrame(omc_rows), hide_index=True, width="stretch")

    st.error(
        f"⚠️ **KILDEKONFLIKT — ikke løst her.** Radene over gir samlet innbetalt "
        f"**${omc_paid:.1f}M** og udekket **${omc_rem:.0f}M**. Fronten "
        f"(`h1-rapport-bruton-analyse-2026-08-13.md`) oppgir **~${OMC_PAID_FRONT:.0f}M "
        f"innbetalt og ${OMC_UNCOVERED_FRONT:.0f}M udekket**. Avviket lar seg ikke "
        f"avstemme med tallene jeg holder: CIMC-terminene er dokumentert fra primærkilder "
        f"(børsmelding 20.03.2026: 10 % ved kontrakt = $49,9M; CIMC-pressemelding "
        f"18.05.2026: 20 % ved stålkutting = $99,8M, til sammen $149,7M) — altså alene "
        f"mer enn frontens $97M for alle åtte. Og $97M + $1 062M = $1 159M mot en samlet "
        f"kontraktssum på $971M for de åtte. **Dette må avklares mot H1-regnskapets egen "
        f"note før OMC-benet brukes til noe.** Per CLAUDE.md går prosjektmappen foran "
        f"wikien ved konflikt — men her peker wikiens tall på primærkilder, så jeg lar "
        f"begge stå synlig i stedet for å velge.",
        icon="🚨",
    )

    q1, q2 = st.columns(2)
    with q1:
        omc_cash = st.number_input("Netto kontanter i OMC ($M)", min_value=-200.0,
                                   max_value=400.0, value=10.0, step=5.0,
                                   help="Motstykket til rest-Brutons. OMC må betale "
                                        "~$23M i 2026-instalments på 2029-skipene, og "
                                        "har ingen inntekter før 2028.")
    with q2:
        omc_haircut = st.slider(
            "Risikorabatt OMC (%)", min_value=0, max_value=70, value=30, step=5,
            help="SKJØNN, ikke aritmetikk. Belåningsgraden kanselleres matematisk ut av "
                 "NAV-formelen, så finansieringsrisikoen KAN ikke fanges der — den må inn "
                 "her. Dekker: (1) restkapex er ufinansiert, og feiler finansieringen må "
                 "egenkapital hentes eller kontrakter selges; (2) 2–3 år uten kontantstrøm; "
                 "(3) Growth-notering med tynn likviditet. Sett 0 for ren substansverdi.",
        )

    omc_nav_usd = (omc_val + omc_cash) * (1 - omc_haircut / 100.0)
    omc_nav_nok = omc_nav_usd * usdnok
    omc_nav_ps = omc_nav_nok / BRUT_SHARES_M

    d1, d2, d3 = st.columns(3)
    d1.metric("Substansverdi før rabatt", f"${omc_val + omc_cash:.0f}M")
    d2.metric("NAV etter rabatt", f"{omc_nav_nok:,.0f} M NOK".replace(",", " "))
    d3.metric("NAV per aksje", f"{omc_nav_ps:.1f} NOK")

    st.caption(
        "Frontens lesning: hele det ufinansierte programmet følger OMC ut, og **det er "
        "nettopp fisjonens funksjon** — den skreller av det som ellers ville sperret "
        "rest-Brutons hovedlisteopptak. H1-noten kobler «fully financed» eksplisitt til "
        "fullført OMC-fisjon."
    )

# ---------------------------------------------------------------------------
# RTO
# ---------------------------------------------------------------------------
st.divider()
st.subheader("RTO-forutsetninger — rest-Bruton inn i 2020B-skallet")

col1, col2 = st.columns(2)
with col1:
    st.markdown("**2020B skall (post-utbytte)**")
    shell_val = st.slider(
        "Antatt RTO-verdi (NOK M)", min_value=20, max_value=400, value=76, step=1,
        help="Verdivurdering-2020B-skall-jul2026.docx: triangulert NOK 60–90M, "
             "scenariovektet E[V] ~76M, likvidasjonsgulv 35–39M. Ingen "
             "august-oppdatering av skallvurderingen finnes i prosjektmappen.",
    )
    cancel_done = st.checkbox(
        "Sletting av 2 791 163 egne aksjer vedtatt (AGM 25. aug)", value=True,
        help="Ikke vedtatt ennå. Uten sletting fordeles samme totalverdi på 22,93M "
             "aksjer → skallkursen faller ~12 %.",
    )
    shell_shares = SHARES_POST_CANCEL_M if cancel_done else SHARES_PRE_CANCEL_M
    st.caption(f"Aksjer i skallet: **{shell_shares:.2f}M**")

with col2:
    st.markdown("**Rest-Bruton**")
    nav_multiple = st.slider(
        "Markedsmultiplikator (× NAV)", min_value=0.60, max_value=1.50, value=0.90, step=0.05,
        help="Fronten bruker 0,85–1,00 × NAV i peer-benet: begrenset track record, "
             "85–90 % LTV og MTF-notering tilsier rabatt; månedlig utbytteprofil, to "
             "charterdekkede skip og Trøim-sfærens historikk trekker motsatt vei. "
             "Rabatten bør lukkes ved hovedlistenotering/RTO.",
    )
    use_nav = st.checkbox("Bruk NAV-estimat som kurs", value=True,
                          help="Rest-Brutons kurs er ikke observerbar før fisjonen er "
                               "gjennomført og det har gått dager til uker med faktisk "
                               "omsetning i to papirer. Det er nettopp derfor et "
                               "bytteforhold ikke kan settes i august.")
    if use_nav:
        brut_price = nav_ps * nav_multiple
        st.metric("Rest-Bruton kurs (avledet)", f"{brut_price:.2f} NOK",
                  help=f"NAV {nav_ps:.2f} × {nav_multiple:.2f}")
    else:
        brut_price = st.slider("Rest-Bruton kurs (NOK)", min_value=10.0, max_value=90.0,
                               value=float(round(nav_ps * nav_multiple, 1)), step=0.5)

brut_shares = BRUT_SHARES_M
brut_mcap = brut_price * brut_shares
combined = brut_mcap + shell_val
brut_pct = brut_mcap / combined * 100
shell_pct = shell_val / combined * 100
shell_pps = shell_val / shell_shares
exchange_ratio = brut_price / shell_pps
total_shares = shell_shares + brut_shares * exchange_ratio
combined_pps = combined / total_shares
cash_shell_pps = shell_cash_nok_m / shell_shares
listing_premium = max(0.0, shell_val - shell_cash_nok_m)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Rest-Bruton eier", f"{brut_pct:.1f} %")
m2.metric("Utvanning for Bruton", f"{shell_pct:.1f} %")
m3.metric("Bytteforhold", f"{exchange_ratio:.2f}x")
m4.metric("Implisitt kurs post-RTO", f"{combined_pps:.2f} NOK")

st.caption(
    f"Frontens §8: med midtpunkt ~2,2 mrd kan et annonsert bytteforhold regnes tilbake "
    f"til implisitt verdi per Bruton-aksje og måles mot **NOK 31–43 som rimelighetsintervall**. "
    f"Vesentlige avvik utenfor intervallet er et signal om enten informasjon vi mangler "
    f"eller et skjevt bytteforhold. Utvanningen ({shell_pct:.1f} %) skal måles mot den "
    f"**varige** rabattforskjellen mellom hovedliste og Growth — anslått ~7 %."
)

# ---------------------------------------------------------------------------
# Posisjon
# ---------------------------------------------------------------------------
st.divider()
if my_brut + my_2020b > 0:
    st.subheader("Din posisjon — før fisjon, etter fisjon, etter RTO")

    brut_cost = my_brut * my_brut_cost
    shell_cost = my_2020b * my_2020b_cost
    total_cost = brut_cost + shell_cost

    pd_rest = my_brut * brut_price
    pd_omc = my_brut * omc_nav_ps
    pd_total = pd_rest + pd_omc

    brut_post_shares = my_brut * exchange_ratio
    brut_post_value = brut_post_shares * combined_pps
    shell_post_value = my_2020b * combined_pps
    total_post = brut_post_value + shell_post_value + pd_omc
    total_pnl = total_post - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0.0

    p1, p2 = st.columns(2)
    with p1:
        st.markdown("**Bruton-eksponering**")
        if my_brut > 0:
            st.metric("Kostnad (GAV)", f"{brut_cost:,.0f} NOK".replace(",", " "))
            st.metric("Rest-Bruton etter fisjon", f"{pd_rest:,.0f} NOK".replace(",", " "),
                      help=f"{my_brut:,} × {brut_price:.2f} NOK".replace(",", " "))
            st.metric("OMC Tankers etter fisjon", f"{pd_omc:,.0f} NOK".replace(",", " "),
                      help=f"Antar 1:1 — fisjonsratio ikke publisert. "
                           f"{omc_nav_ps:.2f} NOK/aksje etter {omc_haircut} % risikorabatt.")
            st.metric("Sum etter fisjon", f"{pd_total:,.0f} NOK".replace(",", " "),
                      delta=f"{pd_total - brut_cost:+,.0f} NOK "
                            f"({(pd_total / brut_cost - 1) * 100 if brut_cost else 0:+.1f}%) "
                            f"vs. GAV".replace(",", " "))
            st.metric("Rest-Bruton-aksjer post-RTO",
                      f"{round(brut_post_shares):,}".replace(",", " "),
                      help=f"× {exchange_ratio:.2f}x bytteforhold")
            st.caption(
                f"⓵ NOK-verdien gjennom selve RTO-en er per definisjon uendret ved fair "
                f"exchange. Den ekte kostnaden er **{shell_pct:.1f} % utvanning** mot "
                f"oppsiden fra hovedlistestatus."
            )
        else:
            st.info("Ingen BRUT-posisjon registrert.")

    with p2:
        st.markdown("**2020B-eksponering (skall)**")
        if my_2020b > 0:
            st.metric("Kostnad (GAV)", f"{shell_cost:,.0f} NOK".replace(",", " "))
            st.metric("Verdi ved antatt skallverdi",
                      f"{my_2020b * shell_pps:,.0f} NOK".replace(",", " "),
                      help=f"Skallkurs {shell_pps:.2f} NOK")
            st.metric("Kun kontanter (gulv)",
                      f"{my_2020b * cash_shell_pps:,.0f} NOK".replace(",", " "),
                      help=f"{cash_shell_pps:.2f} NOK/aksje")
            st.metric("Verdi post-RTO", f"{shell_post_value:,.0f} NOK".replace(",", " "),
                      delta=f"{shell_post_value - shell_cost:+,.0f} NOK "
                            f"({(shell_post_value / shell_cost - 1) * 100 if shell_cost else 0:+.1f}%) "
                            f"vs. GAV".replace(",", " "))
            st.caption(
                f"Break-even skallverdi: GAV × {shell_shares:.2f}M = "
                f"**{my_2020b_cost * shell_shares:.1f}M NOK**. Nesten hele verdien over "
                f"gulvet er betinget av at skallet faktisk anvendes."
            )
        else:
            st.info("Ingen 2020B-posisjon registrert.")

    if total_cost > 0:
        st.success(
            f"**Totalt: kostnad {total_cost:,.0f} → {total_post:,.0f} NOK "
            f"({total_pnl:+,.0f}, {total_pnl_pct:+.1f} %)** — inkl. OMC-benet.".replace(",", " ")
        )
    st.divider()

# ---------------------------------------------------------------------------
# Eierandel + detaljer
# ---------------------------------------------------------------------------
st.subheader("Eierandel i kombinert selskap")
b1, b2 = st.columns([max(brut_pct, 0.5), max(shell_pct, 0.5)])
b1.markdown(f'<div style="background:#1D9E75;color:#fff;padding:12px;'
            f'border-radius:8px 0 0 8px;text-align:center;font-weight:500;">'
            f'Rest-Bruton {brut_pct:.1f}%</div>', unsafe_allow_html=True)
b2.markdown(f'<div style="background:#378ADD;color:#fff;padding:12px;'
            f'border-radius:0 8px 8px 0;text-align:center;font-weight:500;">'
            f'2020B {shell_pct:.1f}%</div>', unsafe_allow_html=True)

st.divider()
left, right = st.columns(2)
with left:
    st.subheader("Transaksjonsdetaljer")
    details = {
        "Scenario": scenario,
        "NAV-metode nybygg": "inkl. SLB-refusjon" if bruk_refusjon else "frontens",
        "Rest-Bruton NAV": f"{nav_nok:,.0f} M NOK ({nav_ps:.1f} kr)",
        "Rest-Bruton markedsverdi": f"{brut_mcap:,.0f} M NOK ({nav_multiple:.2f}×)",
        "OMC Tankers (etter rabatt)": f"{omc_nav_nok:,.0f} M NOK ({omc_nav_ps:.1f} kr)",
        "RTO-verdi skall": f"{shell_val:,.0f} M NOK",
        f"  herav kontanter (US${SHELL_CASH_USD_M:.0f}M)": f"~{shell_cash_nok_m:.1f} M NOK",
        "  herav noteringspremie": f"~{listing_premium:.1f} M NOK",
        "Skallpris per aksje": f"{shell_pps:.2f} NOK",
        "Cash-only pris per aksje": f"{cash_shell_pps:.2f} NOK",
        "Kombinert markedsverdi": f"{combined:,.0f} M NOK",
        "Totalt aksjer post-RTO": f"{total_shares:,.1f} M",
    }
    for k, v in details.items():
        st.markdown(f"**{k}:** {v}".replace(",", " "))

with right:
    st.subheader("Scenariotabell — skallverdi")
    my_cost = my_brut * my_brut_cost + my_2020b * my_2020b_cost
    rows = []
    for sv in [shell_cash_nok_m, 60, 76, 90, 120, 150, 200]:
        spps = sv / shell_shares
        er = brut_price / spps
        cpps = (brut_mcap + sv) / (shell_shares + brut_shares * er)
        post = my_brut * er * cpps + my_2020b * cpps + my_brut * omc_nav_ps
        rows.append({
            "Skall (M NOK)": f"{sv:.0f}",
            "Skallkurs": f"{spps:.2f}",
            "Utvanning": f"{sv / (brut_mcap + sv) * 100:.1f} %",
            "Bytte": f"{er:.2f}x",
            "Din verdi": f"{post:,.0f}".replace(",", " "),
            "vs. GAV": f"{post - my_cost:+,.0f}".replace(",", " ") if my_cost > 0 else "—",
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.caption(
        "Første rad = likvidasjonsgulvet (kun kontanter). NOK ~150M er break-even der "
        "utvanningskostnaden spiser opp den anslåtte reprisingsgevinsten."
    )

# ---------------------------------------------------------------------------
# Fotnote
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "**Kilder.** NAV-benet: `Verdivurdering-Nye-Bruton-aug2026.docx` (13. aug 2026, "
    "H1-oppdatert) — kontraktspriser, gjenstående instalments, MV-bånd, kontantanker, "
    "charterverdi, USD/NOK 9,49. Skallbenet: `Verdivurdering-2020B-skall-jul2026.docx` "
    "(10. juli, ingen august-oppdatering). Hendelser: "
    "`h1-rapport-bruton-analyse-2026-08-13.md`, "
    "`_kilde-finansavisen-bruton-splitt-2026-08-13.md`, "
    "`omc-tankers-lei-registration-2026-08-14.md`. "
    "\n\n"
    "**Status 16. august 2026.** Fisjon annonsert 7. juli. OMC Tankers Ltd. inkorporert "
    "15. juli (Bermuda, reg. 202606135), LEI utstedt 3. august, opptak søkt Euronext "
    "Growth Oslo 14. august (melding 679850, depotbevis) — åtte dager fra styrevedtak til "
    "inkorporering leser som gjennomføringstempo, ikke stillstand. H1 2026: nettoresultat "
    "$0,3M; «subject to completion of the demerger, the Company is fully financed». "
    "Bruton AGM 12. august var ren rutineagenda; 2020B AGM 25. august har **ingen "
    "kapitalforhøyelse** på agendaen. Hard falsifikasjonsgrense flyttet fra utgangen av "
    "september til **medio oktober** (Svensen: «slutten av september eller begynnelsen av "
    "oktober»). Neste dokument: OMCs opptaksdokument — ratio, aksjeantall, kontantsplitt. "
    "\n\n"
    "**Markedsdata medio 2026:** nybygg ~$132M, resale ~$172M (Veson Nautical via "
    "bransjepresse). Svensen: OMC-snitt kontraktskost $121,5M/skip, 2029-nybygg ~$130M, "
    "on-water >$180M per stort meglerhus. Bruton 61 923 808 aksjer (925 000 opsjoner "
    "utestående, ubetydelig utvanning). "
    "\n\n"
    "⓵ I en matematisk fair exchange er NOK-verdien for en Bruton-eier uendret gjennom "
    "selve RTO-en. Skrivebordsøvelse uten selskapstilgang — ikke fairness opinion. "
    "**Dette er ikke investeringsråd.**"
)
