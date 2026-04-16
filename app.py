import streamlit as st


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _risk_from_inputs(tenure_months: int, qa_score: float, overtime_hours: int, satisfaction: int) -> dict:
    """
    Prosta logika (PoC): przelicza wejścia na ryzyko odejścia w skali 0-100%.
    """
    # Sygnały ryzyka (0..1). Wagi są dobrane heurystycznie pod PM-owskie decyzje.
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

    if risk_percent >= 66:
        color = "czerwony"
        label = "WYSOKIE RYZYKO (Czerwona rekomendacja)"
        recommendation = (
            "Natychmiastowa interwencja: 1:1 rozmowa + plan doszkalania (QA) + korekta obciążenia "
            "(nadgodziny/grafik) + wsparcie w onboarding'u. Ustal konkretne cele na 14 dni."
        )
        severity = "error"
    elif risk_percent >= 33:
        color = "zolty"
        label = "SREDNIE RYZYKO (Zolta rekomendacja)"
        recommendation = (
            "Interwencja w krótkim czasie: rozmowa do 7 dni + mentoring + kontrola trendu QA "
            "i satysfakcji. Zmniejsz przeciążenie, zanim ryzyko przejdzie w czerwone."
        )
        severity = "warning"
    else:
        color = "zielony"
        label = "NISKIE RYZYKO (Zielona rekomendacja)"
        recommendation = (
            "Rutynowy follow-up: standardowy coaching i monitoring. Utrzymuj stabilność grafiku oraz "
            "jakosc pracy (QA), zeby ryzyko nie roslo w kolejnych tygodniach."
        )
        severity = "success"

    # Sygnały do wyjaśnienia wyniku (Top-2).
    components = {
        "staz (wczesny onboarding)": tenure_factor,
        "QA (%)": qa_factor,
        "nadgodziny/mies.": overtime_factor,
        "satysfakcja (1-10)": satisfaction_factor,
    }
    top2 = sorted(components.items(), key=lambda kv: kv[1], reverse=True)[:2]

    return {
        "risk_percent": risk_percent,
        "label": label,
        "color": color,
        "recommendation": recommendation,
        "severity": severity,
        "top_signals": top2,
        "factors": {
            "tenure_factor": tenure_factor,
            "qa_factor": qa_factor,
            "overtime_factor": overtime_factor,
            "satisfaction_factor": satisfaction_factor,
        },
    }


def main() -> None:
    st.set_page_config(page_title="CCIG Employee Churn Predictor", layout="centered")
    st.title("CCIG Employee Churn Predictor")
    st.caption("Prototyp (PoC): prosta logika ryzyka dla PM-a. Do produkcji potrzebny model walidowany na danych.")

    st.subheader("Wejścia (suwaki)")
    tenure_months = st.slider("Staz pracy (miesiace)", min_value=0, max_value=36, value=6, step=1)
    qa_score = st.slider("Wynik QA (%)", min_value=0, max_value=100, value=75, step=1)
    overtime_hours = st.slider(
        "Liczba nadgodzin w miesiacu",
        min_value=0,
        max_value=60,
        value=5,
        step=1,
    )
    satisfaction = st.slider(
        "Wynik satysfakcji pracownika (1-10)",
        min_value=1,
        max_value=10,
        value=7,
        step=1,
    )

    st.subheader("Ocena ryzyka i rekomendacja PM")

    result = _risk_from_inputs(
        tenure_months=tenure_months,
        qa_score=float(qa_score),
        overtime_hours=int(overtime_hours),
        satisfaction=int(satisfaction),
    )

    risk_percent = result["risk_percent"]
    label = result["label"]
    recommendation = result["recommendation"]
    top_signals = result["top_signals"]

    if result["severity"] == "error":
        st.error(f"{label}: {risk_percent}%")
    elif result["severity"] == "warning":
        st.warning(f"{label}: {risk_percent}%")
    else:
        st.success(f"{label}: {risk_percent}%")

    st.write("Rekomendacja dla PM-a:")
    st.write(recommendation)

    st.markdown("Najmocniejsze sygnaly w tym scenariuszu:")
    sig_text = ", ".join([f"{name} ({value:.2f})" for name, value in top_signals])
    st.info(sig_text)

    with st.expander("Jak dziala uproszczony scoring (dla komisji)"):
        st.write(
            "Model liczy ryzyko jako wazona sume czterech sygnalow (staz, QA, nadgodziny, satysfakcje). "
            "Nastepnie przypina wynik do progu kolorow: zielony <33%, zolty 33-65%, czerwony >=66%."
        )


if __name__ == "__main__":
    main()

