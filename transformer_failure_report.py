"""Generate a realistic Transformer Failure Analysis PDF report."""
from fpdf import FPDF
import os

class ReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "CONFIDENTIAL - Internal Engineering Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def chapter_title(self, title):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(20, 60, 120)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def section_title(self, title):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(40, 40, 40)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5.5, text)
        self.ln(3)

    def bullet(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.cell(8)
        self.cell(5, 5.5, "-")
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def table_row(self, cols, widths, bold=False):
        self.set_font("Helvetica", "B" if bold else "", 9)
        h = 7
        for i, col in enumerate(cols):
            self.cell(widths[i], h, col, border=1, align="C" if bold else "L")
        self.ln(h)


def build_report():
    pdf = ReportPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # -- COVER PAGE --
    pdf.add_page()
    pdf.ln(50)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(20, 60, 120)
    pdf.cell(0, 14, "Transformer Failure Analysis", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, "Root Cause Investigation & Corrective Action Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, "Report ID: TFA-2026-0742", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Facility: Greenfield Power Station - Unit 3", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Date of Incident: June 28, 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Report Issued: July 15, 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 8, "Prepared by: Dr. Anita Sharma, Lead Reliability Engineer", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Reviewed by: James O'Connor, VP of Asset Management", align="C", new_x="LMARGIN", new_y="NEXT")

    # -- 1. EXECUTIVE SUMMARY --
    pdf.add_page()
    pdf.chapter_title("1. Executive Summary")
    pdf.body_text(
        "On June 28, 2026, the 230/69 kV, 150 MVA main power transformer (Asset ID: TX-GF-003) "
        "at Greenfield Power Station experienced a catastrophic winding failure during peak load "
        "conditions. The failure resulted in an unplanned outage of Unit 3 lasting 14 days, "
        "an estimated revenue loss of $4.2 million, and collateral damage to the 69 kV bus "
        "section B switchgear. No personnel injuries were reported, but environmental containment "
        "protocols were activated due to a 1,200-gallon mineral oil spill from the ruptured "
        "conservator tank."
    )
    pdf.body_text(
        "This report documents the root cause investigation, presents dissolved gas analysis (DGA) "
        "trend data showing precursor warnings as early as March 2026, and proposes corrective and "
        "preventive actions to avoid recurrence across the fleet of 22 similar ABB TRAX-series "
        "transformers deployed at company facilities."
    )

    # -- 2. ASSET PROFILE --
    pdf.chapter_title("2. Asset Profile & Service History")
    w = [45, 145]
    rows = [
        ("Parameter", "Value"),
        ("Manufacturer", "ABB Ltd. - TRAX 150 Series"),
        ("Serial Number", "ABB-TRAX-2009-44821"),
        ("Rated Power", "150 MVA (ONAN) / 180 MVA (ONAF)"),
        ("Voltage Ratio", "230 kV / 69 kV, Delta-Wye-Grounded"),
        ("Cooling", "ONAN / ONAF (dual-stage fans)"),
        ("Year Commissioned", "2009 (17 years in service)"),
        ("Insulation Class", "Class A (105 deg C thermal limit)"),
        ("Oil Volume", "18,500 gallons Nytro Lyra X mineral oil"),
        ("Tap Changer", "MR Type M, 33-position OLTC"),
        ("Last Major Overhaul", "April 2021 - oil reclamation & gasket replacement"),
        ("Maintenance Regime", "Predictive (DGA quarterly, thermal scan monthly)"),
    ]
    for i, (a, b) in enumerate(rows):
        pdf.table_row([a, b], w, bold=(i == 0))

    pdf.ln(4)
    pdf.body_text(
        "TX-GF-003 has historically been a mid-performing asset within the fleet, with a "
        "Health Index score of 72/100 as of Q1 2026. The unit had been flagged in the 2024 "
        "fleet review for elevated moisture content (28 ppm in oil), but remediation was "
        "deferred to the 2027 planned outage window."
    )

    # -- 3. INCIDENT TIMELINE --
    pdf.add_page()
    pdf.chapter_title("3. Incident Timeline")
    w2 = [35, 155]
    timeline = [
        ("Time", "Event"),
        ("14:22", "SCADA alarm: Winding temperature 98 deg C (normal limit 95 deg C)"),
        ("14:25", "Cooling fans stage-2 activated automatically"),
        ("14:31", "Sudden pressure relay (SPR) trip - transformer de-energized"),
        ("14:31", "Buchholz relay gas alarm followed by trip within 3 seconds"),
        ("14:32", "Differential relay (87T) operated - fault current 12.4 kA"),
        ("14:33", "Oil spill detected - conservator tank rupture, ~1,200 gal released"),
        ("14:35", "Fire suppression (deluge) activated; fire contained in 8 min"),
        ("14:42", "Environmental spill response on-site; oil booms deployed"),
        ("15:10", "Unit 3 out-of-service; load transferred to Unit 4 and tie-lines"),
        ("17:00", "Incident Commander established; root cause investigation started"),
    ]
    for i, (a, b) in enumerate(timeline):
        pdf.table_row([a, b], w2, bold=(i == 0))

    # -- 4. ROOT CAUSE ANALYSIS --
    pdf.ln(6)
    pdf.chapter_title("4. Root Cause Analysis")

    pdf.section_title("4.1 Physical Examination Findings")
    pdf.body_text(
        "Internal inspection after oil draining revealed a complete turn-to-turn short circuit "
        "in the high-voltage (HV) winding, Phase B, between layers 14 and 15 (counting from the "
        "core outward). The fault zone exhibited severe carbonization over an area of approximately "
        "120 sq cm, with copper conductor melting visible at the arc initiation point. The "
        "inter-turn insulation (Nomex 410 pressboard spacers, 3.2 mm nominal thickness) was "
        "reduced to less than 0.5 mm at the failure point, indicating long-term thermal degradation."
    )

    pdf.section_title("4.2 Dissolved Gas Analysis (DGA) Trend")
    pdf.body_text(
        "Quarterly DGA records reveal a progressive increase in fault-indicator gases beginning "
        "in Q3 2025, with an accelerating trend in Q1-Q2 2026. The following table summarizes "
        "key gas concentrations (all values in ppm):"
    )

    w3 = [30, 22, 22, 22, 22, 22, 22, 30]
    dga_header = ["Date", "H2", "CH4", "C2H2", "C2H4", "C2H6", "CO", "TDCG"]
    dga_data = [
        ["Q1 2025", "45", "12", "0", "18", "8", "320", "403"],
        ["Q2 2025", "52", "14", "0", "22", "9", "340", "437"],
        ["Q3 2025", "88", "25", "2", "41", "12", "410", "578"],
        ["Q4 2025", "134", "38", "5", "67", "16", "480", "740"],
        ["Q1 2026", "210", "55", "12", "105", "22", "590", "994"],
        ["Q2 2026*", "385", "98", "42", "198", "35", "720", "1478"],
    ]

    pdf.table_row(dga_header, w3, bold=True)
    for row in dga_data:
        pdf.table_row(row, w3)

    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 5, "* Sample collected June 15, 2026 - 13 days before failure.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.body_text(
        "The Duval Triangle analysis of the Q2 2026 sample places the fault signature firmly in "
        "zone DT (thermal fault > 700 deg C combined with electrical discharge). The acetylene "
        "(C2H2) concentration of 42 ppm confirms active arcing was occurring at least two weeks "
        "prior to catastrophic failure. IEEE C57.104-2019 Condition 4 thresholds were exceeded "
        "by Q1 2026, yet the asset was not de-energized for inspection."
    )

    pdf.section_title("4.3 Moisture & Insulation Degradation")
    pdf.body_text(
        "Oil moisture was measured at 38 ppm at the time of failure (versus 28 ppm in 2024 and "
        "the recommended limit of 20 ppm for 230 kV class transformers). Furan analysis showed "
        "2-furfuraldehyde (2-FAL) concentration at 4.8 mg/L, indicating an estimated remaining "
        "paper insulation DP (degree of polymerization) of approximately 250 - well below the "
        "end-of-life threshold of 200 DP. The combination of elevated moisture and thermally "
        "degraded cellulose insulation created conditions for accelerated aging: moisture lowers "
        "the dielectric strength of oil-paper insulation by approximately 0.5% per ppm above "
        "the 20 ppm baseline."
    )

    pdf.section_title("4.4 Contributing Factors")
    pdf.bullet(
        "Overloading: Unit 3 operated at 112% of nameplate rating for 6 hours on June 28 due "
        "to Unit 5 being offline for scheduled maintenance. The N-1 contingency plan assumed "
        "TX-GF-003 could sustain 120% for 4 hours, but did not account for degraded insulation."
    )
    pdf.bullet(
        "Deferred maintenance: The 2024 fleet review recommended oil reclamation and moisture "
        "extraction, but budget constraints deferred this to the 2027 outage window."
    )
    pdf.bullet(
        "Cooling system partial failure: Post-incident inspection found 3 of 8 ONAF cooling "
        "fans (Fan Bank B) had seized bearings, reducing effective cooling capacity by ~18%. "
        "This was not detected because the fan-status SCADA point had been in alarm-suppressed "
        "mode since a nuisance alarm event in February 2026."
    )
    pdf.bullet(
        "DGA response gap: Although the Q1 2026 DGA sample exceeded IEEE Condition 4, the "
        "automated DGA alert was routed to a shared inbox that was not actively monitored after "
        "organizational restructuring in January 2026."
    )

    # -- 5. FAILURE MODE --
    pdf.add_page()
    pdf.chapter_title("5. Failure Mode Classification")
    pdf.body_text(
        "Using the IEEE C57.125 failure classification framework, this event is categorized as:"
    )
    w4 = [50, 140]
    fm = [
        ("Attribute", "Classification"),
        ("Failure Mode", "Dielectric - Turn-to-turn winding fault"),
        ("Cause Category", "Insulation aging (thermal + moisture)"),
        ("Trigger", "Overload above degraded insulation capability"),
        ("Severity", "Major - asset destruction (non-repairable)"),
        ("Consequential Damage", "69 kV bus B switchgear arc flash damage"),
        ("Detection Gap", "DGA Condition 4 alert not actioned"),
    ]
    for i, (a, b) in enumerate(fm):
        pdf.table_row([a, b], w4, bold=(i == 0))

    # -- 6. FINANCIAL IMPACT --
    pdf.ln(6)
    pdf.chapter_title("6. Financial & Operational Impact")
    w5 = [90, 50]
    costs = [
        ("Item", "Cost (USD)"),
        ("Replacement transformer (emergency procurement)", "$3,800,000"),
        ("Installation, commissioning & testing", "$420,000"),
        ("69 kV switchgear repair", "$285,000"),
        ("Environmental remediation (oil spill)", "$175,000"),
        ("Lost generation revenue (14 days)", "$4,200,000"),
        ("Penalty for grid reliability deviation", "$350,000"),
        ("Total Estimated Cost", "$9,230,000"),
    ]
    for i, (a, b) in enumerate(costs):
        pdf.table_row([a, b], w5, bold=(i == 0 or i == len(costs) - 1))

    # -- 7. CORRECTIVE & PREVENTIVE ACTIONS --
    pdf.add_page()
    pdf.chapter_title("7. Corrective & Preventive Actions (CAPA)")

    pdf.section_title("7.1 Immediate Actions (completed)")
    pdf.bullet("Deployed emergency mobile transformer (75 MVA) to restore partial capacity within 72 hours.")
    pdf.bullet("Emergency procurement of replacement 150 MVA transformer from ABB Zurich (lead time: 10 weeks).")
    pdf.bullet("Full DGA audit of all 22 TRAX-series units across the fleet within 14 days.")
    pdf.bullet("Environmental cleanup and EPA notification completed; no regulatory violations cited.")

    pdf.section_title("7.2 Short-Term Actions (30-90 days)")
    pdf.bullet("Implement online DGA monitoring (Serveron TM8) on all transformers rated above 100 MVA. Estimated cost: $45,000 per unit x 12 units = $540,000.")
    pdf.bullet("Repair or replace all ONAF cooling fans fleet-wide; implement fan-status alarming with no suppression override at the operator level.")
    pdf.bullet("Revise N-1 contingency loading limits to incorporate asset Health Index scores; transformers with HI < 80 shall not exceed 100% nameplate.")
    pdf.bullet("Re-establish dedicated DGA alert monitoring workflow with 24-hour acknowledgment SLA.")

    pdf.section_title("7.3 Long-Term Actions (6-18 months)")
    pdf.bullet("Accelerate oil reclamation for all units with moisture > 20 ppm (8 units identified).")
    pdf.bullet("Deploy fiber-optic distributed temperature sensing (DTS) on the 6 oldest transformers to detect localized hot spots in real time.")
    pdf.bullet("Integrate DGA, thermal, and loading data into the predictive analytics platform (IndustryIQ) to enable automated risk scoring and early warning.")
    pdf.bullet("Develop a transformer fleet replacement capital plan with a 10-year horizon, prioritizing units with DP < 350.")

    # -- 8. LESSONS LEARNED --
    pdf.ln(4)
    pdf.chapter_title("8. Lessons Learned")
    pdf.body_text(
        "1. DGA is a leading indicator, not just a lagging metric. The data clearly showed a "
        "developing fault 9 months before failure. Organizations must ensure that condition-monitoring "
        "alerts reach decision-makers with enforced response SLAs.\n\n"
        "2. Deferred maintenance on critical assets carries compounding risk. The $175,000 oil "
        "reclamation deferred in 2024 would have mitigated a $9.2 million failure event - a "
        "53:1 cost ratio.\n\n"
        "3. Auxiliary systems (cooling fans) are single points of failure. Alarm suppression "
        "of any protection-adjacent system must require formal Management of Change (MOC) approval.\n\n"
        "4. Asset Health Index must be dynamically integrated into operational planning. Static "
        "annual reviews are insufficient for aging fleets under variable loading."
    )

    # -- 9. APPENDICES --
    pdf.add_page()
    pdf.chapter_title("9. Appendices")

    pdf.section_title("Appendix A - Key Terminology")
    terms = [
        ("DGA", "Dissolved Gas Analysis - measurement of gases dissolved in transformer oil to diagnose internal faults."),
        ("TDCG", "Total Dissolved Combustible Gas - sum of H2, CH4, C2H2, C2H4, C2H6, and CO."),
        ("Buchholz", "A gas-actuated relay on oil-filled transformers to detect internal faults producing gas."),
        ("DP", "Degree of Polymerization - cellulose insulation condition; new paper ~1200, end-of-life ~200."),
        ("OLTC", "On-Load Tap Changer - a device that regulates output voltage under load."),
        ("Duval Tri.", "Diagnostic method plotting three key gases (CH4, C2H2, C2H4) to classify fault types."),
        ("ONAN/ONAF", "Oil Natural Air Natural / Oil Natural Air Forced - transformer cooling modes."),
        ("HI", "Health Index - composite score (0-100) aggregating condition data to rank asset risk."),
        ("ppm", "Parts per million - concentration unit for dissolved gases and moisture in oil."),
        ("2-FAL", "2-Furfuraldehyde - byproduct of cellulose thermal degradation; estimates paper life."),
    ]
    w6 = [30, 160]
    pdf.table_row(["Term", "Definition"], w6, bold=True)
    for abbr, defn in terms:
        pdf.table_row([abbr, defn], w6)

    pdf.ln(6)
    pdf.section_title("Appendix B - Referenced Standards")
    pdf.bullet("IEEE C57.104-2019: Guide for Interpretation of Gases Generated in Mineral Oil-Immersed Transformers")
    pdf.bullet("IEEE C57.125-2015: Guide for Failure Investigation, Documentation, Analysis, and Reporting for Power Transformers")
    pdf.bullet("IEC 60599:2022: Mineral oil-filled electrical equipment in service - Guidance on DGA interpretation")
    pdf.bullet("IEEE C57.91-2011: Guide for Loading Mineral Oil-Immersed Transformers and Step-Voltage Regulators")

    pdf.ln(4)
    pdf.section_title("Appendix C - Distribution List")
    pdf.bullet("Dr. Anita Sharma - Lead Reliability Engineer (Author)")
    pdf.bullet("James O'Connor - VP, Asset Management (Reviewer)")
    pdf.bullet("Sarah Chen - Director, Grid Operations")
    pdf.bullet("Mike Torres - Environmental Health & Safety Manager")
    pdf.bullet("ABB Service Engineering - Transformer failure feedback (copy)")

    # -- Save --
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Transformer_Failure_Analysis_TFA-2026-0742.pdf")
    pdf.output(out_path)
    print(f"PDF saved to: {out_path}")

if __name__ == "__main__":
    build_report()
