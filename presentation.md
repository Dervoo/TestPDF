## Slajd 1/12 — Project Vision
- **Project Vision:** proaktywne zarządzanie rotacją w CCIG dzięki predykcji odejść w oparciu o dane z kampanii.
- Redukcja churn przed wypowiedzeniem: PM dostaje alert, kiedy działa najtańsza interwencja (pierwszy etap onboardingu).
- Jeden model, wiele kampanii: wspólny standard diagnozy ryzyka i planu działań.
- Mierzalność od dnia 1: KPI jakości, satysfacji i produktywności zamiast „czucia menedżera”.

## Slajd 2/12 — Analiza otoczenia biznesowego (PESTEL: 4 trendy)
- **Koszty pracy rosną szybciej niż budżety:** presja płac + koszty rekrutacji i onboardingu (ok. **5000 PLN** na konsultanta).
- **Technologia:** AI obniża koszt decyzji operacyjnych, ale podnosi oczekiwania (szybkość, personalizacja, predykcja).
- **Rynek pracownika:** skrócone cykle zatrudnienia i większa wrażliwość na frustrację w hybrydzie.
- **Omnichannel i standardy compliance:** dane z wielu kanałów i procesów muszą trafiać do jednego, spójnego obrazu ryzyka.

## Slajd 3/12 — Wyzwanie nr 1 i 2
- **Rosnące koszty operacyjne:** rośnie koszt „naprawiania” rotacji po fakcie (rekrutacja + ponowny onboarding).
- **Spadek jakości w modelu hybrydowym:** rozproszenie zespołu utrudnia kalibrację QA i szybkie coachingi.
- Zmienia się rytm pracy: teamy wymagają krótszych pętli informacji zwrotnej, a nie raportów cyklicznych „po wszystkim”.
- Ryzyko jakości rośnie w okresach przeciążenia: nadgodziny i spadek satysfakcji idą w parze z churn.

## Slajd 4/12 — Wyzwanie nr 3: krytyczna rotacja na wczesnym etapie
- **Wysoka rotacja (Employee Churn) na wczesnym etapie życia pracownika**: pierwsze tygodnie i miesiące decydują o przyszłej stabilności zespołu.
- Koszt utraconej inwestycji w onboarding jest bezpośredni: ok. **5000 PLN** na zastąpienie jednego konsultanta.
- Średnia miesięczna rotacja w CC w Polsce bywa **5–15%**: przy wzroście churnu rosną koszty i ryzyko spadku jakości.
- PM musi reagować wcześniej: decyzje „po zdarzeniu” są droższe i mniej skuteczne.

## Slajd 5/12 — Autorskie rekomendacje 1 i 2
- Rekomendacja 1: **korekta pracy i harmonogramów na podstawie obciążenia** (nadgodziny → ryzyko jakości i wypalenia).
- Rekomendacja 2: **program kalibracji QA w trybie hybrydowym** (standardy kontroli, mikro-coachingi, szybkie zamykanie pętli feedbacku).
- Automatyzacja omnichannel: jedna baza wiedzy + jeden szablon działań PM (co robić, gdy ryzyko rośnie).
- Efekt: mniej „gaszenia pożaru”, więcej sterowania jakością i retencją w czasie.

## Slajd 6/12 — Rekomendacja nr 3: Data-Driven Retention
- **Data-Driven Retention:** model predykcyjny churnu, który pokazuje ryzyko odejścia zanim pojawi się wypowiedzenie.
- Uczenie na danych historycznych: etykieta churn (zdarzenia HR) + cechy z operacji i jakości (staż, QA, obciążenie, satysfakcja).
- PM dostaje rekomendację w 2 krokach: (1) procentowe ryzyko, (2) kolorowa akcja (zielona/żółta/czerwona).
- Cel: proaktywna interwencja w „oknie onboardingu”, kiedy koszt reakcji jest najniższy.

## Slajd 7/12 — Architektura ekosystemu PM-a
- Źródła danych z kampanii CCIG: wyniki **QA**, ankiety satysfakcji, metryki operacyjne (w tym nadgodziny) oraz dane HR o stażu.
- Pipeline danych do modelu: normalizacja → cechy → predykcja → zapis wyników w module PM.
- „Sterowanie decyzją”: alerty i rekomendacje trafiają do PM wraz z uzasadnieniem sygnałów (żeby dało się to obronić na spotkaniu).
- Pętla doskonalenia: feedback od PM i wyniki po wdrożeniu wracają do kalibracji modelu.

## Slajd 8/12 — DEMO LIVE (QR Code + narracja kandydata)
- Skanujesz **QR** i testujesz prototyp: „Employee Churn Predictor” w aplikacji webowej.
- Ustawiasz suwaki: **staż pracy**, **QA %**, **nadgodziny/mies.**, **satysfakcja (1–10)**.
- Aplikacja pokazuje: **procentowe ryzyko odejścia** + alert dla PM (zielony/żółty/czerwony) z krótką rekomendacją działań.
- Skrypt/narracja (ok. 3 zdania): „Proszę o szybki test: proszę zeskanować kod QR i ustawić parametry na suwakach, które odzwierciedlają realny profil konsultanta. Aplikacja zwróci procentowe ryzyko odejścia oraz kolorową rekomendację dla PM-a wraz z kierunkiem działania. Chodzi o to, żeby reagować wcześniej i obniżyć churn zanim stanie się kosztownym zdarzeniem operacyjnym.”

## Slajd 9/12 — Business Case (zysk miesięczny z redukcji churn)
Założenia: zespół **100 os.**, koszt zastąpienia 1 konsultanta **5000 PLN**, model ML obniża rotację o **15%**.

| Wariant | Rotacja miesięczna | Odejścia/mies. (z 100) | Koszt wymiany (PLN/mies.) |
|---|---:|---:|---:|
| Stan obecny | 10% | 10.0 | 50 000 |
| Stan po wdrożeniu ML | 8.5% | 8.5 | 42 500 |
| **Miesięczny zysk (oszczędność)** | 15% mniej | 1.5 mniej | **7 500 PLN** |

- Miesięczna oszczędność wynika z mniejszej liczby odejść i stałego kosztu zastąpienia (5000 PLN/os.).
- Model nie „zgaduje w ciemno”: ryzyko jest wyliczane z sygnałów, które PM może realnie skorygować (coach, obciążenie, QA, wsparcie w onboarding’u).
- Następny krok to dopięcie ROI na podstawie kosztów utrzymania narzędzia i efektów na KPI jakości.

## Slajd 10/12 — Roadmapa wdrożenia (30-60-90 dni, Agile)
- **0–30 dni (Audyt):** mapowanie danych (HR/QA/satysfakcja/nadgodziny), przegląd procesów PM i zdefiniowanie etykiety churn.
- **31–60 dni (MVP/PoC):** model predykcyjny w wersji testowej + dashboard alertów dla PM na wybranej kampanii.
- **61–90 dni (Skalowanie):** kalibracja na wynikach PoC, standaryzacja procesu interwencji i roll-out na pełny projekt.
- W każdym oknie sprintu: test „czy PM działa lepiej” (czas reakcji, trafność alertów, efekt na rotację).

## Slajd 11/12 — Zarządzanie ryzykiem
- Ryzyko: **opór zespołu przed wdrażaniem nowych rozwiązań** (obawa, że system służy do inwigilacji).
- Mitigacja: komunikacja od pierwszego dnia — narzędzie ma wspierać, a nie karać; PM pokazuje, że to poprawia warunki pracy i jakość wsparcia.
- Mitigacja: zasady użycia danych i transparentny proces interwencji (co robimy przy alertach i dlaczego).
- Mitigacja: szybkie „proof points” z PoC (krótszy Time-to-Proficiency, stabilniejsze QA, wzrost satysfakcji).

## Slajd 12/12 — Podsumowanie i miary sukcesu (KPI)
- **eNPS:** czy zmiany w procesie wsparcia realnie poprawiają morale i poczucie sensu pracy.
- **Time-to-Proficiency:** czy konsultanci szybciej osiągają pełną samodzielność dzięki lepszej reakcji PM na sygnały ryzyka.
- **ROI:** (uniknięte koszty churnu zredukowane przez ML - koszt utrzymania systemu) / koszt utrzymania systemu.
- Cel końcowy: mniej churnu, lepsza jakość i przewidywalny onboarding w warunkach hybrydowych.

