[KONTEKST I ROLA]
Działaj jako Senior Project Manager i ekspert ds. strategii w branży outsourcingu Contact Center. Twoim zadaniem jest wygenerowanie kompletnego, merytorycznego wsadu do 30-minutowej prezentacji rekrutacyjnej dla CCIG Group. Oprócz prezentacji, przygotujesz również kod do narzędzia wspomagającego pracę PM-a.

[ZASADY GENEROWANIA TREŚCI - GUARDRAILS]
- Zero lania wody: Używaj krótkich, żołnierskich zdań. 
- Twarde dane: Opieraj się na realiach polskiego rynku CC (np. koszt rekrutacji i onboardingu konsultanta to ok. 5000 PLN; średnia rotacja miesięczna to 5-15%).
- Formatowanie: Wynik musi być surowym kodem Markdown. Używaj nagłówków, pogrubień dla wskaźników (KPI) oraz tabel.
- Brak wstępów: Nie pisz powitań. Wygeneruj od razu gotowy materiał.

[STRUKTURA PREZENTACJI - 12 SLAJDÓW]
Zbuduj dokładnie 12 slajdów według poniższych wytycznych. Dla każdego napisz Tytuł i 3-4 mocne bullet-pointy z konkretną treścią.

CZĘŚĆ I: Diagnoza Rynku (Slajdy 1-4)
- Slajd 1: Tytuł i "Project Vision".
- Slajd 2: Analiza otoczenia biznesowego (PESTEL - wypunktuj 4 trendy: koszty pracy, AI, rynek pracownika, omnichannel).
- Slajd 3: Wyzwania nr 1 i 2 (Skup się na rosnących kosztach operacyjnych i spadku jakości w modelu hybrydowym).
- Slajd 4: Wyzwanie nr 3 - Krytyczna rotacja (Employee Churn) na wczesnym etapie i koszty utraconej inwestycji w onboarding.

CZĘŚĆ II: Rozwiązania i Technologia (Slajdy 5-8)
- Slajd 5: Autorskie rekomendacje 1 i 2 (Dopasowane do wyzwań z rynkowych z poprzednich slajdów).
- Slajd 6: Rekomendacja 3 - "Data-Driven Retention" (Podejście oparte na uczeniu maszynowym do proaktywnego zapobiegania rotacji).
- Slajd 7: Architektura Ekosystemu PM-a (Jak dane z kampanii CCIG zasilają model).
- Slajd 8: DEMO LIVE (Slajd z kodem QR). Dodaj tu dokładny skrypt/narrację (ok. 3 zdań), co kandydat ma powiedzieć, wręczając komisji tablet z działającym prototypem "Employee Churn Predictor".

CZĘŚĆ III: Biznes i Wdrożenie (Slajdy 9-12)
- Slajd 9: Business Case (Zbuduj tabelę z modelem finansowym: zespół 100 os., koszt wdrożenia 1 os. to 5000 PLN, założenie: model ML obniża rotację o 15%. Pokaż stan obecny, stan po wdrożeniu i miesięczny zysk).
- Slajd 10: Roadmapa Wdrożenia (Plan 30-60-90 dni: Audyt - MVP/PoC - Skalowanie).
- Slajd 11: Zarządzanie Ryzykiem (Zidentyfikuj opór zespołu jako ryzyko i podaj plan mitygacji poprzez komunikację).
- Slajd 12: Podsumowanie i Miary Sukcesu (Kluczowe KPI: eNPS, Time-to-Proficiency, ROI).

[KOD APLIKACJI - PO ZAKOŃCZENIU PREZENTACJI]
Po wygenerowaniu wszystkich 12 slajdów, w oddzielnym bloku kodu dostarcz gotowy do uruchomienia kod w Pythonie (Streamlit) dla narzędzia "CCIG Employee Churn Predictor".
Wymagania dla kodu:
- Interfejs musi być w języku polskim.
- Musi zawierać suwaki: Staż pracy (miesiące), Wynik QA (%), Liczba nadgodzin w miesiącu, Wynik satysfakcji pracownika z ostatniej ankiety (1-10).
- Napisz uproszczoną logikę, która przelicza te wartości na procentowe ryzyko odejścia i wyświetla czerwoną/żółtą/zieloną alertową rekomendację dla PM-a.