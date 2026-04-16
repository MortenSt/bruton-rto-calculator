import streamlit as st

st.set_page_config(page_title="Bruton / 2020B RTO Dilution", page_icon="🚢", layout="wide")

st.title("Bruton × 2020 Bulkers — RTO dilution-kalkulator")
st.caption("Basert på børsmelding 16. april 2026: spesialutbytte US$13,8/aksje = NOK 129,5/aksje. ~US$4M beholdes i skallet.")

CASH_IN_SHELL_NOK = 37.5  # ~US$4M at USD/NOK 9.384
USDNOK = 129.5 / 13.8

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("2020B skall (post-utbytte)")
    shell_val = st.slider("Skallverdi (NOK M)", min_value=20, max_value=300, value=50, step=5,
                          help="Kontanter ~37,5M + noteringspremie")
    shell_shares = st.slider("Aksjer etter tilbakekjøp (M)", min_value=18.0, max_value=22.93, value=22.0, step=0.1,
                             help="22,93M før tilbakekjøp 17–22. april")

with col2:
    st.subheader("Bruton")
    brut_price = st.slider("BRUT kurs (NOK)", min_value=35.0, max_value=80.0, value=52.0, step=0.5)
    brut_shares = st.slider("BRUT aksjer (M)", min_value=55.0, max_value=70.0, value=61.9, step=0.1,
                            help="61,9M etter feb-2026 PP")

with col3:
    st.subheader("Din posisjon")
    my_brut = st.number_input("Dine BRUT-aksjer", min_value=0, max_value=100_000, value=4_000, step=100)

st.divider()

# --- calculations ---
brut_mcap = brut_price * brut_shares  # in M NOK
shell_mcap = shell_val  # M NOK
combined = brut_mcap + shell_mcap

brut_pct = brut_mcap / combined * 100
shell_pct = shell_mcap / combined * 100

shell_price_per_share = shell_val / shell_shares
exchange_ratio = brut_price / shell_price_per_share
new_shares = brut_shares * exchange_ratio  # M
total_shares = shell_shares + new_shares

my_pct_brut = my_brut / (brut_shares * 1e6) * 100
my_pct_combined = my_pct_brut * (brut_pct / 100)
my_new_shares = round(my_brut * exchange_ratio)

listing_premium = max(0, shell_val - CASH_IN_SHELL_NOK)

# --- display ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("BRUT-aksjonærer eier", f"{brut_pct:.1f} %", help="Andel av kombinert selskap")
m2.metric("Dilution for BRUT", f"{shell_pct:.1f} %", help="Gitt til 2020B skall-aksjonærer")
m3.metric("Bytteforhold", f"{exchange_ratio:.1f}x", help="Nye aksjer per BRUT-aksje")
m4.metric("Dine aksjer post-RTO", f"{my_new_shares:,}".replace(",", " "), help=f"Fra {my_brut:,} BRUT-aksjer")

st.divider()

# Ownership bar
st.subheader("Eierandel i kombinert selskap")
bar_col1, bar_col2 = st.columns([brut_pct, max(shell_pct, 0.5)])
bar_col1.markdown(
    f'<div style="background:#1D9E75;color:#fff;padding:12px;border-radius:8px 0 0 8px;text-align:center;font-weight:500;">'
    f'Bruton {brut_pct:.1f}%</div>', unsafe_allow_html=True)
bar_col2.markdown(
    f'<div style="background:#378ADD;color:#fff;padding:12px;border-radius:0 8px 8px 0;text-align:center;font-weight:500;">'
    f'2020B {shell_pct:.1f}%</div>', unsafe_allow_html=True)

st.divider()

# Details table
left, right = st.columns(2)

with left:
    st.subheader("Transaksjonsdetaljer")
    data = {
        "Bruton markedsverdi": f"{brut_mcap:,.0f} M NOK",
        "Skallverdi (antatt)": f"{shell_mcap:,.0f} M NOK",
        "  herav kontanter (~$4M)": f"~{CASH_IN_SHELL_NOK:.1f} M NOK",
        "  herav noteringspremie": f"~{listing_premium:.1f} M NOK",
        "Skallpris per aksje": f"{shell_price_per_share:.1f} NOK",
        "Kombinert markedsverdi": f"{combined:,.0f} M NOK",
        "Totalt aksjer post-RTO": f"{total_shares:,.1f} M",
    }
    for k, v in data.items():
        st.markdown(f"**{k}:** {v}")

with right:
    st.subheader("Scenariotabell")
    import pandas as pd
    scenarios = []
    for sv in [37.5, 50, 75, 100, 150, 200, 300]:
        b_pct = brut_mcap / (brut_mcap + sv) * 100
        s_pct = 100 - b_pct
        er = brut_price / (sv / shell_shares)
        scenarios.append({
            "Skallverdi (M)": f"{sv:.0f}",
            "BRUT eier": f"{b_pct:.1f}%",
            "2020B eier": f"{s_pct:.1f}%",
            "Bytteforhold": f"{er:.1f}x",
        })
    st.dataframe(pd.DataFrame(scenarios), hide_index=True, use_container_width=True)

st.divider()
st.caption(
    f"Kontantverdi i skallet: ~US$4M ≈ NOK 37,5M (USD/NOK {USDNOK:.2f}). "
    f"Utbytte NOK 129,5/aksje (korrigert). Ex-dato 29. april. "
    f"Tilbakekjøp 17–22. april til NOK 129,5/aksje. "
    f"Bruton: 61.923.808 aksjer etter feb-2026 PP."
)
