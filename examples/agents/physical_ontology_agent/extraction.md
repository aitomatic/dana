# Equipment Inventory

| ID      | Type                  | Location                | Notes                                              |
|---------|-----------------------|-------------------------|----------------------------------------------------|
| AHU-01  | Air Handling Unit     | AHU-01 Room (4-F)       | 22,150 CFM, serves South-West quadrant (Zone 1)    |
| AHU-02  | Air Handling Unit     | AHU-02 Room (4-J)       | 23,600 CFM, serves North-West quadrant (Zone 2)    |
| AHU-03  | Air Handling Unit     | AHU-03 Room (6-J)       | 23,100 CFM, serves North-East quadrant (Zone 3)    |
| AHU-04  | Air Handling Unit     | AHU-04 Room (6-F)       | 20,750 CFM, serves South-East quadrant (Zone 4)    |
| VAV-01  | Variable Air Volume   | NW Office (2-3, K-L)    | Connected to AHU-02                                |
| VAV-02  | Variable Air Volume   | NW Office (2-3, K-L)    | Connected to AHU-02                                |
| VAV-03  | Variable Air Volume   | NW Office (2-3, K-L)    | Connected to AHU-02                                |
| VAV-04  | Variable Air Volume   | NW Office (2-3, K-L)    | Connected to AHU-02                                |
| VAV-05  | Variable Air Volume   | NW Office (2-3, K-L)    | Connected to AHU-02                                |
| VAV-06  | Variable Air Volume   | NW Office (2-3, K-L)    | Connected to AHU-02                                |
| VAV-07  | Variable Air Volume   | NE Office (7-9, K-L)    | Connected to AHU-03                                |
| VAV-08  | Variable Air Volume   | NE Office (7-9, K-L)    | Connected to AHU-03                                |
| VAV-09  | Variable Air Volume   | NE Office (7-9, K-L)    | Connected to AHU-03                                |
| VAV-10  | Variable Air Volume   | NE Office (7-9, K-L)    | Connected to AHU-03                                |
| VAV-11  | Variable Air Volume   | SE Office (7-9, E-G)    | Connected to AHU-04                                |
| VAV-12  | Variable Air Volume   | SE Office (7-9, E-G)    | Connected to AHU-04                                |
| VAV-13  | Variable Air Volume   | SW Office (2-4, E-G)    | Connected to AHU-01                                |
| VAV-14  | Variable Air Volume   | SW Office (2-4, E-G)    | Connected to AHU-01                                |
| VAV-15  | Variable Air Volume   | SW Office (2-4, E-G)    | Connected to AHU-01                                |
| VAV-16  | Variable Air Volume   | SW Office (2-4, E-G)    | Connected to AHU-01                                |
| VAV-17  | Variable Air Volume   | SE Office (7-9, E-G)    | Connected to AHU-04                                |
| VAV-18  | Variable Air Volume   | SE Office (7-9, E-G)    | Connected to AHU-04                                |
| FD-01   | Fire Damper           | Core Shafts (5-6, H-J)  | At duct/shaft interface                            |
| VCD-01  | Volume Control Damper | Branch Ducts (2, L)     | Manual, at branch to diffusers                     |
| VCD-02  | Volume Control Damper | Main Ducts              | Manual, at main trunk off VAVs                     |
| MD-01   | Motorized Damper      | Fresh Air Intake (3, J) | At fresh air intake                                |
| MD-02   | Motorized Damper      | Fresh Air Intake (7, J) | At fresh air intake                                |
| TH-01   | Thermostat            | NW Office (2-3, K-L)    | Wall-mounted, zone feedback for VAVs               |
| TH-02   | Thermostat            | NE Office (7-9, K-L)    | Wall-mounted, zone feedback for VAVs               |
| TH-03   | Thermostat            | SW Office (2-4, E-G)    | Wall-mounted, zone feedback for VAVs               |
| TH-04   | Thermostat            | SE Office (7-9, E-G)    | Wall-mounted, zone feedback for VAVs               |
| DS-01   | Duct Sensor           | Main Duct (4, J)        | Static pressure/temp, supply duct from AHU-02       |
| DS-02   | Duct Sensor           | Main Duct (6, J)        | Static pressure/temp, supply duct from AHU-03       |
| DS-03   | Duct Sensor           | Main Duct (4, F)        | Static pressure/temp, supply duct from AHU-01       |
| DS-04   | Duct Sensor           | Main Duct (6, F)        | Static pressure/temp, supply duct from AHU-04       |
| CO2-01  | CO2 Sensor            | Male Toilet (4, H)      | High-density area                                  |
| CO2-02  | CO2 Sensor            | Female Toilet (5, J)    | High-density area                                  |

# Relationships

| Source   | Relationship   | Target    | Notes                                      |
|----------|---------------|-----------|--------------------------------------------|
| AHU-01   | supplies      | VAV-13    | Primary air supply                         |
| AHU-01   | supplies      | VAV-14    | Primary air supply                         |
| AHU-01   | supplies      | VAV-15    | Primary air supply                         |
| AHU-01   | supplies      | VAV-16    | Primary air supply                         |
| AHU-02   | supplies      | VAV-01    | Primary air supply                         |
| AHU-02   | supplies      | VAV-02    | Primary air supply                         |
| AHU-02   | supplies      | VAV-03    | Primary air supply                         |
| AHU-02   | supplies      | VAV-04    | Primary air supply                         |
| AHU-02   | supplies      | VAV-05    | Primary air supply                         |
| AHU-02   | supplies      | VAV-06    | Primary air supply                         |
| AHU-03   | supplies      | VAV-07    | Primary air supply                         |
| AHU-03   | supplies      | VAV-08    | Primary air supply                         |
| AHU-03   | supplies      | VAV-09    | Primary air supply                         |
| AHU-03   | supplies      | VAV-10    | Primary air supply                         |
| AHU-04   | supplies      | VAV-11    | Primary air supply                         |
| AHU-04   | supplies      | VAV-12    | Primary air supply                         |
| AHU-04   | supplies      | VAV-17    | Primary air supply                         |
| AHU-04   | supplies      | VAV-18    | Primary air supply                         |
| VAV-01   | connected_to  | Diffusers | Duct connection                            |
| VAV-02   | connected_to  | Diffusers | Duct connection                            |
| ...      | ...           | ...       | ... (similar for all VAVs to diffusers)    |
| VAV-01   | controlled_by | TH-01     | Thermostat feedback                        |
| VAV-07   | controlled_by | TH-02     | Thermostat feedback                        |
| VAV-13   | controlled_by | TH-03     | Thermostat feedback                        |
| VAV-11   | controlled_by | TH-04     | Thermostat feedback                        |
| AHU-02   | monitored_by  | DS-01     | Duct sensor in supply duct                 |
| AHU-03   | monitored_by  | DS-02     | Duct sensor in supply duct                 |
| AHU-01   | monitored_by  | DS-03     | Duct sensor in supply duct                 |
| AHU-04   | monitored_by  | DS-04     | Duct sensor in supply duct                 |
| Male Toilet | monitored_by | CO2-01   | CO2 sensor in return air                   |
| Female Toilet | monitored_by | CO2-02 | CO2 sensor in return air                   |
| Main Duct | has_damper   | VCD-02    | Volume control damper                      |
| Branch Duct | has_damper | VCD-01    | Volume control damper                      |
| Fresh Air Intake | has_damper | MD-01 | Motorized damper                           |
| Fresh Air Intake | has_damper | MD-02 | Motorized damper                           |
| Duct/Shaft | has_damper  | FD-01     | Fire damper at shaft interface             |

# Spatial Hierarchy

| Space                  | Contains Equipment                                 | Parent Space         |
|------------------------|----------------------------------------------------|----------------------|
| AHU-01 Room (4-F)      | AHU-01, DS-03, MD-01                              | Mechanical Core      |
| AHU-02 Room (4-J)      | AHU-02, DS-01, MD-02                              | Mechanical Core      |
| AHU-03 Room (6-J)      | AHU-03, DS-02                                     | Mechanical Core      |
| AHU-04 Room (6-F)      | AHU-04, DS-04                                     | Mechanical Core      |
| NW Office (2-3, K-L)   | VAV-01, VAV-02, VAV-03, VAV-04, VAV-05, VAV-06, TH-01 | Floor Area NW    |
| NE Office (7-9, K-L)   | VAV-07, VAV-08, VAV-09, VAV-10, TH-02             | Floor Area NE        |
| SW Office (2-4, E-G)   | VAV-13, VAV-14, VAV-15, VAV-16, TH-03             | Floor Area SW        |
| SE Office (7-9, E-G)   | VAV-11, VAV-12, VAV-17, VAV-18, TH-04             | Floor Area SE        |
| Male Toilet (4, H)     | CO2-01                                            | Core                 |
| Female Toilet (5, J)   | CO2-02                                            | Core                 |
| Core Shafts (5-6, H-J) | FD-01                                             | Core                 |
| Branch Ducts (2, L)    | VCD-01                                            | Ceiling Plenum       |
| Main Ducts             | VCD-02                                            | Ceiling Plenum       |
| Fresh Air Intake (3, J)| MD-01                                             | Perimeter            |
| Fresh Air Intake (7, J)| MD-02                                             | Perimeter            |

# Additional Observations

- Some sensor locations are inferred based on standard design, as icons may not be visible at this scale.
- Diffuser and grille IDs are not explicitly labeled; assumed one per VAV branch.
- Piping systems are primarily air ducts; no chilled/hot water or refrigerant piping is shown.
- Fire dampers and volume control dampers are present at all major duct penetrations and branches.
- All AHUs are located in dedicated mechanical rooms at the building core.
- All VAVs are ceiling-mounted in open office zones.
- CO2 sensors are present in high-occupancy toilet areas.
- If more detail is needed on diffuser/grille counts, a higher-resolution image or legend may be required.

