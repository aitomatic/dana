# Study Material: Refrigerator Component Design Specifications

---

## 1. Rubber Gasket (DM-01-B002b) Design Specification

The rubber gasket serves as the compressor's base to absorb vibration and ensure the quiet operation (noise reduction) of the refrigerator.

### Design Objectives and Process

- **Primary Goal:** Prevent compressor vibration from being transmitted to the frame (cross-beam), which causes secondary noise (e.g., casing resonance, internal compartment noise).

#### Design Flow
1. Confirm Quality Report based on technical information.
2. Review Material.
3. Review Shape.
4. Determine the Rubber Gasket Specification.

#### Related Standards
- JIS K 6254
- MIS A 5012

### Vibration Isolation Performance Evaluation

- **Natural Frequency ($f_0$):**
    - $f_0$ is determined by measuring the static deflection ($\delta_{sc}$) of the gasket under the compressor load.
    - **Standard Requirement:** The natural frequency ($f_0$) of the refrigerator (induction type) must be $17\,\text{Hz}$ or less.
    - **Design Principle:** To ensure good vibration isolation, $f_0$ should typically be $1/3$ or less of the excitation frequency ($f$).

- **Vibration Transmissibility ($\tau$):**  
    The vibration transmissibility (without damping) is calculated as:
    $$
    \tau = \frac{1}{(f/f_{0})^{2}-1}
    $$
    [cite: 606]

### Long-Term Reliability Evaluation

| Evaluation Item | Standard / Method | Key Points |
|-----------------|------------------|------------|
| **Compression Permanent Deformation ($CS$)** | Based on JIS K 6254. Compressed to 25% of installed height and heated at $110^\circ \text{C}$ for 22 hours. | The permanent set is calculated by $CS = \frac{t_0 - t_1}{t_0 - t_2} \times 100\%$. |
| **Compressor Actual Installation Test** | Test the elasticity reduction in a $110^\circ \text{C}$ oven. | A 10-year service life is modeled as 28.5 days at $110^\circ \text{C}$ (using the $10^\circ \text{C}$ halving rule). |
| **Shipping Vibration Test** | Based on MIS A-5012. | Evaluate for no abnormal noise before and after the test. |
| **Door Opening Shock Test** | Conducted while the compressor is running. | Confirm the compressor's bottom does not collide with any part of the unit due to the shock. |

---

## 2. Air Duct Design (DM-01-B012a)

Air duct design is one of the three major elements for the refrigerator's basic system design, alongside cabinet design (heat load) and refrigeration design (cooling capacity).

### Design Objectives

- **Total Air Flow Rate ($V_\text{total}$):**  
  Set the total air flow rate to supply the necessary cooling capacity to the interior, corresponding to the cabinet's heat absorption load.

- **Air Flow Rate Allocation ($V_\text{chamber}$):**  
  Set the air flow rate for each chamber, corresponding to its heat absorption load, to cool it to the set temperature.

- **Air Duct Resistance ($R$):**  
  Determine the duct's cross-sectional area, length, and shape to achieve the target $V_\text{total}$ and allocation by setting the appropriate air duct resistance.

### Key Formulas

- **Evaporator Cooling Capacity ($Q$):**
  $$
  Q = V \times \rho \times C_p \times \Delta T \times \phi
  $$
  (1.1) [cite: 729, 730]

  - $V$: Air Flow Rate ($\text{m}^3/\text{min}$)
  - $\rho$: Air Density
  - $C_p$: Specific Heat of Air
  - $\Delta T$: Air-Refrigerant Evaporation Temperature Difference
  - $\phi$: Temperature Efficiency

- **Air Flow Rate in Each Chamber ($V_a$):**
  $$
  Q_L = V_a \times \rho_a \times C_{Pa} \times (T_{ao} - T_{ai}) \times \frac{1000}{60}
  $$
  (2.2) [cite: 796, 798]

  - $Q_L$: Heat absorption load (W)
  - $V_a$: Cold air flow rate into each compartment ($\text{m}^3/\text{min}$)
  - $T_{ao}$: Compartment temperature ($^\circ\text{C}$)
  - $T_{ai}$: Cold air temperature at evaporator outlet ($^\circ\text{C}$)

- **Air Duct Resistance ($R$):**
  $$
  R = \frac{\Delta P}{\alpha \cdot \rho \cdot V^2}
  $$
  (3.1) [cite: 817]

  - $R$: Air Duct Resistance ($\text{min}^2/\text{m}^5$)
  - $\Delta P$: Pressure Loss ($\text{mmAq}$)
  - $\alpha$: Constant (0.08)

---

## 3. Dryer Specification Design (DM-01-B013a)

The dryer is critical for the sealed cooling system to remove moisture, harmful components, and dust, ensuring long-term reliability.

### Dryer Criticality

- **Primary Risk:** Moisture freezing at the capillary tube outlet can cause blockages, impairing cooling function, degrading refrigerating oil, and leading to compressor failure.
- **Secondary Risks:** Molecular sieve powdering due to vibration, filter/capillary tube clogging from generated substances, and corrosion.

### Molecular Sieve Selection and Mass Determination

| Molecule           | Molecular Diameter | Examples of Sieve Pore Size          |
|--------------------|-------------------|--------------------------------------|
| Water ($H_2O$)     | ~2 Å              | XH600, XH7.9, 4AXH-6 (~3 Å)          |
| R134a, R22, R12    | ~4 Å              | 4ANRG, 4AXH-5 (~4 Å)                 |
| R600a              | ~5 Å              | N/A                                  |

- **Selection Rule:** The sieve pore size must be smaller than the refrigerant's molecular diameter but larger than the water molecule's diameter to adsorb water while rejecting the refrigerant.

- **Mass Calculation:**
    $$
    \text{Molecular Sieve Mass} = \frac{\text{Allowable Moisture Mass}}{\text{Adsorption Rate}} \times \text{Safety Factor}
    $$
    [cite: 1008]

- **Allowable Total Moisture (R-134a Example):** $\leq 150\,\text{mg}$ for the entire cooling system.
- **Corporate Data:**
    - Adsorption Rate: $0.185$ (reduced from oil adsorption)
    - Safety Factor: $3$

### Installation and Reliability Guidelines

- **Vibration Control:** The dryer's maximum vibration amplitude must be $\leq 50\,\mu\text{m}$ (in the 40–75 Hz range). Excessive vibration (e.g., over $100\,\mu\text{m}$) can cause molecular sieve powdering.
- **Installation Direction:** Should be horizontal or with the capillary tube side below. Vertical mounting is acceptable only if dust and compounds are confirmed not to cause blockages in the system.

#### Sieve Degradation Risks

- Absorbing over 10% water content causes mechanical strength to rapidly decrease, making it prone to powdering.
- Sieve powder acts as an abrasive and can cause abnormal wear and compressor failure.
- Molecular sieves are alkaline ceramics; in the presence of refrigerant/oil, chemical decomposition can occur, potentially leading to chlorine gas generation (chlorides) and sieve particle decay.
- R-134a using ester oil may generate acid upon hydrolysis (with water).

#### Corrosion Prevention

- For the inlet pipe (if iron), flux must be removed after silver brazing, and epoxy coating must be applied for rust prevention.

