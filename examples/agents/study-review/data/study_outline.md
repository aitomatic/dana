# Comprehensive Refrigerator System Design: Study Outline

This outline is generated from the combined specifications of Rubber Gaskets, Air Duct Design, and Dryer Specifications.

---

## I. Rubber Gasket (Compressor Mount) Design (DM-01-B002b)

**Focus:** Vibration isolation and noise reduction.

### 1. Core Objectives

- **Primary Function:** Acts as the compressor seat to absorb vibration.
- **Key Goal:** Contributes to quiet refrigerator operation (noise reduction).
- **Failure Mode Prevention:** Prevents compressor vibration transmission to the frame (cross-beam), which causes secondary noise (e.g., casing resonance).

### 2. Design Process

- Review material and shape.
- Determine final rubber gasket specification.

### 3. Vibration Isolation Performance Metrics

- **Natural Frequency ($f_0$):**
    - *Definition:* Frequency determined by static deflection ($\delta_{sc}$) under compressor load.
    - *Standard Requirement:* $f_0 \leq 17$ Hz (for induction type refrigerators).
    - *Design Principle:* $f_0$ should be $1/3$ or less of the excitation frequency ($f$).

- **Vibration Transmissibility ($\tau$):**
    - *Formula (without damping):*
        $$
        \tau = \frac{1}{(f/f_0)^2 - 1}
        $$

### 4. Long-Term Reliability and Testing

- **Compression Permanent Deformation ($CS$):**
    - *Standard:* JIS K 6254.
    - *Test Method:* Compress to 25% height, heat at $110^\circ$C for 22 hours.
    - *Calculation:* 
        $$
        CS = \frac{t_0 - t_1}{t_0 - t_2} \times 100\%
        $$
        *(where $t_0$ is original thickness, $t_1$ is post-test thickness, $t_2$ is spacer thickness)*
- **Accelerated Aging Test:** Installation test at $110^\circ$C (28.5 days ≈ 10 years of service life).
- **Shipping Vibration Test (MIS A 5012):** Check for abnormal noise before/after.
- **Door Opening Shock Test:** Confirm no collision between compressor bottom and unit during shock.

---

## II. Air Duct Design (DM-01-B012a)

**Focus:** Ensuring adequate and balanced cooling capacity distribution.

### 1. Role in System Design

- One of the three major elements of basic system design (alongside cabinet heat load and refrigeration cooling capacity).

### 2. Design Objectives

- **Total Air Flow Rate ($V_{total}$):** Set to match cabinet's heat absorption load and to provide necessary total cooling capacity.
- **Air Flow Rate Allocation ($V_{chamber}$):** Set for each chamber to match its specific load and achieve target temperature.
- **Air Duct Resistance ($R$):** Determine duct geometry (cross-sectional area, length, shape) to achieve target air flow rates via appropriate resistance.

### 3. Key Design Formulas

- **Evaporator Cooling Capacity ($Q$):**
    $$
    Q = V \times \rho \times C_p \times \Delta T \times \phi \tag{1.1}
    $$
    *(relates flow rate $V$ to cooling output $Q$)*

- **Chamber Air Flow Rate ($V_a$):**
    $$
    Q_L = V_a \times \rho_a \times C_{Pa} \times (T_{ao} - T_{ai}) \times \left(\frac{1000}{60}\right) \tag{2.2}
    $$
    *(relates chamber heat load $Q_L$ to required flow rate $V_a$)*

- **Air Duct Resistance ($R$):**
    $$
    R = \frac{\Delta P}{\alpha \cdot \rho \cdot V^2} \tag{3.1}
    $$
    *(must be balanced with fan's P-Q characteristic)*

### 4. Fan Selection Guidance

- **High Resistance Ducts:** Use high static pressure fan (for fixed high air volume).
- **Low Resistance Ducts:** Use low static pressure fan (for high air volume).
- **P-Q Curve Consideration:** Test fan's P-Q characteristics under conditions close to actual installation, as single-fan data may be misleading.

---

## III. Dryer Specification Design (DM-01-B013a)

**Focus:** System longevity by removing contaminants, especially moisture.

### 1. Purpose and Criticality

- **Goal:** Remove moisture, harmful components, and dust from the sealed cooling system.
- **Critical Risk:** Moisture freezing at capillary tube outlet causes blockages, loss of cooling, oil degradation, and compressor failure.

### 2. Molecular Sieve Selection

- **Function:** Adsorbs moisture ($\sim$2 Å) while rejecting refrigerant (e.g., R-134a $\sim$4 Å).
- **Selection Rule:** Sieve pore size must be smaller than the refrigerant but larger than water.
- **Example Sieves:** XH600, XH7.9, 4AXH-6 (pore size $\sim$3 Å).

### 3. Molecular Sieve Mass Calculation

- **Mass Formula:**
    $$
    \text{Mass} = \frac{\text{Allowable Moisture Mass}}{\text{Adsorption Rate}} \times \text{Safety Factor}
    $$

- **Typical Values (R-134a):**
    - *Allowable Total Moisture:* $\leq 150$ mg
    - *Adsorption Rate:* Estimated at $0.185$ (due to oil absorption)
    - *Safety Factor:* $3$

### 4. Installation and Reliability Guidelines

- **Vibration Control:** Max amplitude $\leq 50\,\mu$m (40–75 Hz) to prevent powdering.
- **Installation Direction:** Horizontal or capillary tube side below.
- **Sieve Degradation:**
    - *Water Content:* $>10\%$ absorption leads to rapid mechanical strength loss and powdering.
    - *Chemical Risk:* Molecular sieves (alkaline ceramics) can react with refrigerant/oil, leading to acid formation (R-134a/ester oil) and possible chlorine gas generation.
- **Corrosion Prevention:** Iron inlet pipes require flux removal after brazing and application of epoxy coating or rubber blocks for rust prevention.


