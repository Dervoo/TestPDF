import streamlit as st
import plotly.graph_objects as go


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _risk_from_inputs(tenure_months: int, qa_score: float, overtime_hours: int, satisfaction: int) -> dict:
    """
    Logika PoC: przelicza wejścia na ryzyko odejścia w skali 0-100%.
    """
    # Staż: ryzyko jest najwyższe na początku (okno ~0-6 miesięcy).
    tenure_factor = _clamp((6 - tenure_months) / 6, 0, 1)
    # QA: niższy wynik zwiększa ryzyko.
    qa_factor = (100 - qa_score) / 100
    # Nadgodziny: im więcej, tym większe ryzyko przeciążenia.
    overtime_factor = _clamp(overtime_hours / 40, 0, 1)
    # Satysfakcja: im niższa, tym większe ryzyko odejścia.
    satisfaction_factor = (10 - satisfaction) / 9

    w_tenure = 0.35
    w_qa = 0.35
    w_overtime = 0.15
    w_satisfaction = 0.15

    risk_unit = (
        tenure_factor * w_tenure
        + qa_factor * w_qa
        + overtime_factor * w_overtime
        + satisfaction_factor * w_satisfaction
    )

    risk_percent = int(round(risk_unit * 100))
    risk_percent = int(_clamp(risk_percent, 0, 100))

    return {
        "risk_percent": risk_percent,
        "factors": {
            "tenure": tenure_factor,
            "qa": qa_factor,
            "overtime": overtime_factor,
            "satisfaction": satisfaction_factor,
        },
    }


def main() -> None:
    st.set_page_config(
        page_title="CCIG Employee Churn Predictor",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🚀 CCIG Employee Churn Predictor")
    st.markdown("---")

    # Layout: Lewa kolumna (Wejścia), Prawa kolumna (Analiza i Rekomendacje)
    col_input, col_output = st.columns([1, 1.2], gap="large")

    with col_input:
        st.subheader("📊 Parametry Agenta")
        st.info("Dostosuj suwaki, aby przeanalizować ryzyko odejścia pracownika.")
        
        tenure_months = st.slider("Staż pracy (miesiące)", 0, 36, 6)
        qa_score = st.slider("Wynik QA (%)", 0, 100, 75)
        overtime_hours = st.slider("Nadgodziny w miesiącu", 0, 60, 5)
        satisfaction = st.slider("Wynik satysfakcji (1-10)", 1, 10, 7)

        st.markdown("---")
        with st.expander("ℹ️ Metodologia"):
            st.write(
                "Algorytm analizuje 4 kluczowe wymiary: Onboarding (Staż), "
                "Efektywność (QA), Obciążenie (Overtime) oraz Morale (Satysfakcja)."
            )

    # Obliczenia
    result = _risk_from_inputs(tenure_months, float(qa_score), overtime_hours, satisfaction)
    risk_percent = result["risk_percent"]
    factors = result["factors"]

    with col_output:
        st.subheader("🔍 Wynik Analizy Ryzyka")

        # 1. Gauge Chart (Wykres zegarowy)
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=risk_percent,
            title={'text': "Prawdopodobieństwo Churnu (%)", 'font': {'size': 20}},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "#31333F"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 33], 'color': '#28a745'},  # Zielony
                    {'range': [33, 66], 'color': '#ffc107'}, # Żółty
                    {'range': [66, 100], 'color': '#dc3545'} # Czerwony
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': risk_percent
                }
            }
        ))
        fig.update_layout(height=350, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)

        # 2. Kalkulator Ryzyka Finansowego
        base_cost = 6000
        # Logika: Przy wysokim ryzyku (>66%) koszt jest prezentowany jako niemal pewna strata
        if risk_percent > 66:
            at_risk_capital = base_cost
        else:
            at_risk_capital = (risk_percent / 100.0) * base_cost
        
        st.metric(
            label="⚠️ Zagrożony Kapitał (Koszty Rotacji)", 
            value=f"{at_risk_capital:,.2f} PLN",
            delta=f"przy koszcie bazowym {base_cost} PLN",
            delta_color="inverse"
        )

        st.markdown("---")

        # 3. Dynamiczne "Action Plan" (Rekomendacje)
        st.subheader("📝 Plan Działania dla PM-a")
        
        recommendations = []
        
        if satisfaction <= 3:
            recommendations.append("🚨 **Krytyczne!** Przeprowadź spotkanie 1:1 w ciągu najbliższych 24h. Wynik satysfakcji jest alarmująco niski.")
        
        if overtime_hours > 20:
            recommendations.append("📉 **Przeciążenie:** Zredukuj obciążenie w grafiku. Ryzyko wypalenia z powodu nadmiernej liczby nadgodzin.")
        
        if qa_score < 60:
            recommendations.append("🎓 **Rozwój:** Zaplanuj sesję kalibracyjną i odsłuchy z trenerem. Spadek jakości rzutuje na pewność siebie agenta.")
            
        if tenure_months <= 3 and risk_percent > 50:
            recommendations.append("🐣 **Onboarding:** Zintensyfikuj opiekę mentorską. Agent jest w fazie 'szoku po-szkoleniowego'.")

        if not recommendations:
            if risk_percent < 20:
                st.success("Wszystkie wskaźniki w normie. Rekomendacja: Standardowy feedback motywacyjny.")
            else:
                st.info("Monitoruj sytuację. Brak krytycznych odchyleń, ale wskaźnik ryzyka jest podwyższony.")
        else:
            for rec in recommendations:
                st.write(rec)


if __name__ == "__main__":
    main()
