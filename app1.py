import streamlit as st
import pandas as pd

st.set_page_config(page_title="Bruton / 2020B RTO Dilution", page_icon="🚢", layout="wide")
st.title("Bruton × 2020 Bulkers — RTO dilution-kalkulator")
st.caption("Basert på børsmelding 16. april 2026: spesialutbytte US$13,8/aksje = NOK 129,5/aksje. ~US$4M beholdes i skallet.")

CASH_IN_SHELL_NOK = 37.5  # ~US$4M at USD/NOK 9.384
USDNOK_DEFAULT = 129.5 / 13.8

# --- sidebar: posisjon (per-investor inputs) ---
with st.sidebar:
    st.header("Din posisjon")
    st.markdown("**Bruton (BRUT)**")
    my_brut = st.number_input("BRUT-aksjer", min_value=0, max_value=10_000_000, value=1_000, step=100, key="brut_qty")
    my_brut_cost = st.number_input("GAV BRUT (NOK)", min_value=0.0, max_value=200.0, value=50.0, step=0.5)
    st.markdown("---")
    st.markdown("**2020 Bulkers (2020B) — skall post-utbytte**")
    my_2020b = st.number_input("2020B-aksjer", min_value=0, max_value=10_000_000, value=1_000, step=100, key="b20_qty")
    my_2020b_cost = st.number_input("GAV 2020B post-utbytte (NOK)", min_value=0.0, max_value=20.0, value=2.5, step=0.1,
                                    help="Cash-only intrinsic verdi: ~1,7 NOK ved 22M aksjer.")
    st.markdown("---")
    st.caption(
        "GAV = gjennomsnittlig anskaffelseskurs. La feltene stå på 0 for grupper du ikke eier. "
        "For 2020B post-utbytte: kjøpskurs **etter** at NOK 129,5 utbytte er trukket fra."
    )

# --- main: RTO-forutsetninger ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("2020B skall (post-utbytte)")
    shell_val = st.slider("Antatt RTO-verdi (NOK M)", min_value=20, max_value=300, value=44, step=1,
                          help="Verdsettelsen som forhandles i RTO. Kontanter ~37,5M + ev. noteringspremie.")
    shell_shares = st.slider("Aksjer etter tilbakekjøp (M)", min_value=18.0, max_value=22.93, value=22.0, step=0.05,
                             help="22,93M før tilbakekjøp 17–22. april")

with col2:
    st.subheader("Bruton")
    brut_price = st.slider("BRUT kurs (NOK)", min_value=35.0, max_value=120.0, value=52.0, step=0.5,
                           help="Justerbar opp til 120 NOK for NAV-baserte scenarier (RTO-tidspunkt med Mount Vision levert)")
    brut_shares = st.slider("BRUT aksjer (M)", min_value=55.0, max_value=70.0, value=61.9, step=0.1,
                            help="61,9M etter feb-2026 PP")

st.divider()

# --- NAV-modul ---
with st.expander("📊 Bruton NAV-modell — intrinsic value-estimat", expanded=False):
    st.markdown(
        "Estimer Bruton-aksjens NAV basert på flåteverdi og balanse. "
        "Standardverdier reflekterer **august 2026** (Mount Vision på vannet, 11 nybygg under bygging) "
        "og Q1 2026 Clarksons-data: VLCC newbuild $128,5M, modern resale $168M (+$39,5M premie)."
    )

    n1, n2, n3 = st.columns(3)
    with n1:
        st.markdown("**På vannet**")
        on_water_ships = st.number_input("Skip levert", min_value=0, max_value=12, value=1, step=1,
                                         help="Aug 2026: 1 (Mount Vision). Jan 2027: 2. Per skipsleveringer fra New Times og CIMC Raffles fram til 2029.")
        resale_value = st.number_input("Resale-verdi per skip ($M)", min_value=100.0, max_value=250.0, value=175.0, step=5.0,
                                       help="Q1 2026: $168M for moderne VLCC. Mount Vision: LNG dual-fuel + scrubber → ~$175-180M.")
        delivery_ltv = st.slider("Leveringsfinansiering LTV (%)", min_value=50, max_value=80, value=65, step=1,
                                 help="Typisk 60-70% for VLCC. ECA/yard-finansiering kan være høyere.")

    with n2:
        st.markdown("**Under bygging**")
        nb_count = st.number_input("Antall nybygg", min_value=0, max_value=15, value=11, step=1)
        nb_paid_in = st.number_input("Snitt innbetalt kapex per NB ($M)", min_value=10.0, max_value=120.0, value=35.0, step=5.0,
                                     help=("Grovt snitt over 11 nybygg på ulike stadier i aug 2026: "
                                           "1 nær levering (~$95M), 2 i tidlig konstruksjon (~$60M), "
                                           "rest i tidlige stadier (~$15-30M). Snitt ~$30-40M."))
        slot_premium = st.number_input("Slot-premie per NB ($M)", min_value=-10.0, max_value=40.0, value=0.0, step=2.5,
                                       help=("Verdi over kontraktspris. Bruton's 2027-2029 slots har lite premie i dag — "
                                             "Sinokor-bonansaen har dyttet ordrebok-til-flåte fra 10% til 26%. "
                                             "Kun 2026-slots har stor premie."))

    with n3:
        st.markdown("**Balanse & valuta**")
        net_cash = st.number_input("Netto kontant/(gjeld) ($M)", min_value=-500.0, max_value=300.0, value=-50.0, step=10.0,
                                   help=("Beregnet: total equity raised - capex paid - leveringsfinansiering. "
                                         "Negativ = netto gjeld. Estimat etter feb-2026 PP og innbetalinger til verft."))
        usdnok_nav = st.number_input("USD/NOK", min_value=8.0, max_value=12.0, value=9.40, step=0.05)
        nav_multiple = st.slider("Markedsmultiplikator (× NAV)", min_value=0.7, max_value=1.5, value=1.0, step=0.05,
                                 help=("Hvordan markedet typisk priser pure-play tankereiere: "
                                       "0,8-0,9× i bear, 1,0× ved fair value, 1,1-1,3× i hete markeder, "
                                       "1,3-1,5× ved supercycle-multiple-ekspansjon."))

    # NAV-beregning
    on_water_equity = on_water_ships * resale_value * (1 - delivery_ltv / 100)
    nb_equity = nb_count * (nb_paid_in + slot_premium)
    total_nav_usd = on_water_equity + nb_equity + net_cash
    total_nav_nok = total_nav_usd * usdnok_nav
    nav_per_share = (total_nav_nok / brut_shares) if brut_shares > 0 else 0  # M NOK / M shares = NOK

    fair_value_per_share = nav_per_share * nav_multiple
    market_vs_nav = (brut_price / nav_per_share - 1) * 100 if nav_per_share > 0 else 0
    market_vs_fair = (brut_price / fair_value_per_share - 1) * 100 if fair_value_per_share > 0 else 0

    st.divider()
    nav1, nav2, nav3, nav4 = st.columns(4)
    nav1.metric("På vannet (egenkapital)", f"${on_water_equity:.0f}M")
    nav2.metric("Nybygg (egenkapital)", f"${nb_equity:.0f}M")
    nav3.metric("NAV per aksje", f"{nav_per_share:.1f} NOK",
                help=f"Total NAV: {total_nav_nok:,.0f} M NOK (${total_nav_usd:.0f}M)".replace(",", " "))
    nav4.metric("Fair value (×multiplikator)", f"{fair_value_per_share:.1f} NOK",
                delta=f"{-market_vs_fair:+.1f}% fra dagens kurs")

    if abs(market_vs_fair) > 5:
        if market_vs_fair < 0:
            st.success(
                f"💡 Markedskursen ({brut_price:.1f} NOK) handler **{-market_vs_fair:.1f}% under** fair value "
                f"({fair_value_per_share:.1f} NOK). Ved RTO i hetebølgen (aug 2026) kan BRUT-kursen reprises "
                f"oppover. **Vurder å sette BRUT-kurs slideren over til {fair_value_per_share:.0f} NOK** for å "
                f"modellere et RTO-scenario der markedet har priset inn re-rating."
            )
        else:
            st.warning(
                f"💡 Markedskursen ({brut_price:.1f} NOK) handler **{market_vs_fair:.1f}% over** fair value. "
                f"Enten priser markedet inn ekstra premie (RTO/NYSE), eller forutsetningene i NAV-modellen "
                f"er for konservative."
            )

    st.caption(
        f"**NAV = (skip på vannet × resale × (1−LTV)) + (nybygg × (paid-in + slot-premie)) + netto kontant**. "
        f"Per aksje = NAV NOK / {brut_shares:.1f}M aksjer. "
        f"Disse er grove estimater — uten siste kvartalsregnskap er paid-in capex og netto gjeld de største usikkerhetene."
    )

# --- core RTO calculations ---
brut_mcap = brut_price * brut_shares
combined = brut_mcap + shell_val

brut_pct = brut_mcap / combined * 100
shell_pct = shell_val / combined * 100

shell_price_per_share = shell_val / shell_shares
exchange_ratio = brut_price / shell_price_per_share
new_shares = brut_shares * exchange_ratio
total_shares = shell_shares + new_shares
combined_price_per_share = combined / total_shares

cash_shell_price = CASH_IN_SHELL_NOK / shell_shares

# Posisjonsverdier
brut_cost = my_brut * my_brut_cost
brut_market_value = my_brut * brut_price
brut_post_shares = my_brut * exchange_ratio
brut_post_value = brut_post_shares * combined_price_per_share
brut_pnl = brut_post_value - brut_cost
brut_pnl_pct = (brut_pnl / brut_cost * 100) if brut_cost > 0 else 0

shell_cost = my_2020b * my_2020b_cost
shell_post_value = my_2020b * combined_price_per_share
shell_pnl = shell_post_value - shell_cost
shell_pnl_pct = (shell_pnl / shell_cost * 100) if shell_cost > 0 else 0

total_cost = brut_cost + shell_cost
total_post = brut_post_value + shell_post_value
total_pnl = total_post - total_cost
total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0

listing_premium = max(0, shell_val - CASH_IN_SHELL_NOK)

# --- topp-metrics ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("BRUT eier", f"{brut_pct:.1f} %", help="Andel av kombinert selskap")
m2.metric("Dilution for BRUT", f"{shell_pct:.1f} %", help="Verdi gitt til 2020B-aksjonærer")
m3.metric("Bytteforhold", f"{exchange_ratio:.2f}x", help="Nye aksjer per BRUT-aksje")
m4.metric("Implisitt kurs post-RTO", f"{combined_price_per_share:.2f} NOK")

st.divider()

# --- posisjonspanel ---
if my_brut + my_2020b > 0:
    st.subheader("Din posisjon — pre vs. post-RTO")
    p1, p2 = st.columns(2)

    with p1:
        st.markdown("**Bruton-eksponering**")
        if my_brut > 0:
            st.metric("Kostnad (GAV)", f"{brut_cost:,.0f} NOK".replace(",", " "),
                      help=f"{my_brut:,} × {my_brut_cost:.2f} NOK GAV")
            st.metric("Markedsverdi pre-RTO", f"{brut_market_value:,.0f} NOK".replace(",", " "),
                      help=f"{my_brut:,} × {brut_price:.2f} NOK")
            st.metric("Aksjer post-RTO", f"{round(brut_post_shares):,}".replace(",", " "),
                      help=f"{my_brut:,} × {exchange_ratio:.2f}x bytteforhold")
            st.metric("Verdi post-RTO", f"{brut_post_value:,.0f} NOK".replace(",", " "),
                      delta=f"{brut_pnl:+,.0f} NOK ({brut_pnl_pct:+.1f}%) vs. GAV".replace(",", " "))
            st.caption(
                f"⓵ NOK-verdien gjennom RTO er per def. uendret (fair exchange). "
                f"Den ekte kostnaden er **{shell_pct:.1f}% dilution** mot oppside fra hovedlistestatus."
            )
        else:
            st.info("Ingen BRUT-posisjon registrert.")

    with p2:
        st.markdown("**2020B-eksponering (skall)**")
        if my_2020b > 0:
            st.metric("Kostnad (GAV)", f"{shell_cost:,.0f} NOK".replace(",", " "),
                      help=f"{my_2020b:,} × {my_2020b_cost:.2f} NOK")
            st.metric("Markedsverdi pre-RTO", f"{my_2020b * shell_price_per_share:,.0f} NOK".replace(",", " "),
                      help=f"Ved antatt skallkurs {shell_price_per_share:.2f} NOK")
            st.metric("Aksjer post-RTO", f"{my_2020b:,}".replace(",", " "),
                      help="Samme antall aksjer, ny pris")
            st.metric("Verdi post-RTO", f"{shell_post_value:,.0f} NOK".replace(",", " "),
                      delta=f"{shell_pnl:+,.0f} NOK ({shell_pnl_pct:+.1f}%) vs. GAV".replace(",", " "))
            st.caption(
                f"Break-even RTO-verdi: GAV × {shell_shares:.1f}M = "
                f"**{my_2020b_cost * shell_shares:.1f}M NOK skallverdi**"
            )
        else:
            st.info("Ingen 2020B-posisjon registrert.")

    if total_cost > 0:
        st.markdown(
            f"**Totalt: kostnad {total_cost:,.0f} → post-RTO {total_post:,.0f} NOK "
            f"({total_pnl:+,.0f}, {total_pnl_pct:+.1f}%)**".replace(",", " ")
        )

    st.divider()

# --- ownership bar ---
st.subheader("Eierandel i kombinert selskap")
bar_col1, bar_col2 = st.columns([max(brut_pct, 0.5), max(shell_pct, 0.5)])
bar_col1.markdown(
    f'<div style="background:#1D9E75;color:#fff;padding:12px;border-radius:8px 0 0 8px;'
    f'text-align:center;font-weight:500;">Bruton {brut_pct:.1f}%</div>',
    unsafe_allow_html=True)
bar_col2.markdown(
    f'<div style="background:#378ADD;color:#fff;padding:12px;border-radius:0 8px 8px 0;'
    f'text-align:center;font-weight:500;">2020B {shell_pct:.1f}%</div>',
    unsafe_allow_html=True)

st.divider()

# --- detaljer + scenariotabell ---
left, right = st.columns(2)

with left:
    st.subheader("Transaksjonsdetaljer")
    data = {
        "Bruton markedsverdi": f"{brut_mcap:,.0f} M NOK",
        "RTO-verdi skall": f"{shell_val:,.0f} M NOK",
        "  herav kontanter (~$4M)": f"~{CASH_IN_SHELL_NOK:.1f} M NOK",
        "  herav noteringspremie": f"~{listing_premium:.1f} M NOK",
        "Skallpris per aksje": f"{shell_price_per_share:.2f} NOK",
        "Cash-only pris per aksje": f"{cash_shell_price:.2f} NOK",
        "Kombinert markedsverdi": f"{combined:,.0f} M NOK",
        "Implisitt kurs post-RTO": f"{combined_price_per_share:.2f} NOK",
        "Totalt aksjer post-RTO": f"{total_shares:,.1f} M",
    }
    for k, v in data.items():
        st.markdown(f"**{k}:** {v}")

with right:
    st.subheader("Scenariotabell — total P&L")
    scenarios = []
    for sv in [37.5, 44, 50, 75, 100, 150, 200]:
        spps = sv / shell_shares
        er = brut_price / spps
        cpps = (brut_mcap + sv) / (shell_shares + brut_shares * er)
        brut_post_s = my_brut * er * cpps
        b20_post_s = my_2020b * cpps
        total_post_s = brut_post_s + b20_post_s
        pnl_s = total_post_s - total_cost
        pnl_pct_s = (pnl_s / total_cost * 100) if total_cost > 0 else 0
        scenarios.append({
            "Skall (M)": f"{sv:.0f}",
            "Skallkurs": f"{spps:.2f}",
            "Bytte": f"{er:.2f}x",
            "BRUT post": f"{brut_post_s:,.0f}".replace(",", " "),
            "2020B post": f"{b20_post_s:,.0f}".replace(",", " "),
            "Total P&L": f"{pnl_s:+,.0f} ({pnl_pct_s:+.0f}%)".replace(",", " "),
        })
    st.dataframe(pd.DataFrame(scenarios), hide_index=True, use_container_width=True)
    if total_cost > 0:
        st.caption(f"Basert på samlet kostnad {total_cost:,.0f} NOK".replace(",", " "))

st.divider()

st.caption(
    f"Kontantverdi i skallet: ~US$4M ≈ NOK {CASH_IN_SHELL_NOK:.1f}M (USD/NOK {USDNOK_DEFAULT:.2f}). "
    f"Utbytte NOK 129,5/aksje. Ex-dato 29. april. Tilbakekjøp 17–22. april til NOK 129,5/aksje. "
    f"Bruton: 61.923.808 aksjer etter feb-2026 PP. "
    f"Markedsdata Q1 2026 (Clarksons): VLCC newbuild $128,5M, modern resale $168M. "
    f"Brutons flåte: 8 ved New Times ($138M), 4 ved CIMC Raffles ($124,75M). "
    f"⓵ I en matematisk fair exchange er NOK-verdien for BRUT-holder uendret per def. gjennom selve RTO. "
    f"P&L vs. GAV reflekterer kursutvikling fra kjøpstidspunkt, ikke RTO-effekt isolert. "
    f"Dette er ikke investeringsråd."
)
