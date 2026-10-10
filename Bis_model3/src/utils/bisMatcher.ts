export interface DetectedStandard {
  standardCode: string;
  standardTitle: string;
  category: string;
  scheme: string;
  division: string;
  scopeSummary: string;
  checklist: string[];
}

export const BIS_STANDARDS_CATALOG: DetectedStandard[] = [
  {
    standardCode: 'IS 16221 (Part 2) / IS 16169',
    standardTitle: 'Safety of Power Converters for Photovoltaic Power Systems & Islanding Prevention',
    category: 'Solar & Renewable Equipment',
    scheme: 'Compulsory Registration Scheme (CRS) — MNRE Quality Order',
    division: 'Solar Energy Division (ETD 28)',
    scopeSummary: 'Grid anti-islanding trip time (< 2.0s), DC input isolation (> 1 MΩ at 1000V DC), and full load conversion efficiency (> 95%).',
    checklist: [
      'Anti-Islanding Test Report (IS 16169)',
      'DC Overvoltage & Ground Fault Isolation Report',
      'Manufacturer Factory Registration & QAP',
      'PCB Trace Clearance & Creepage Certificate',
    ],
  },
  {
    standardCode: 'IS 374 : 2019',
    standardTitle: 'Electric Ceiling Type Fans and Regulators — Specification',
    category: 'Household Electrical Appliances',
    scheme: 'DPIIT Quality Control Order (QCO) / Mandatory ISI Scheme',
    division: 'Electrotechnical Division (ETD 32)',
    scopeSummary: 'Minimum air delivery (210 m³/min for 1200mm sweep), BLDC motor service value (5.0 m³/min/W), and 1000N shackle safety pin integrity.',
    checklist: [
      'Air Delivery Wind Tunnel Test Report',
      'Suspension Shackle Tensile Strength Test',
      'Motor Temperature Rise & Insulation Test',
      'BEE Star Rating Registration Dossier',
    ],
  },
  {
    standardCode: 'IS 1293 : 2019 / IS 13252',
    standardTitle: 'Plugs and Socket-Outlets of Rated Voltage up to 250V & Smart IT Safety',
    category: 'Smart Devices & IoT',
    scheme: 'DPIIT QCO & MeitY CRS Mandatory Order',
    division: 'Electrical Accessories (ETD 14)',
    scopeSummary: 'Solid 6A/16A pin dimensional tolerances, 750°C Glow Wire flammability resistance, and 4.0mm creepage distance.',
    checklist: [
      'Pin Dimensional Gauging Report',
      '750°C Glow Wire Heat Test Certificate',
      'Relay High-Voltage Switching Endurance',
      'Factory Calibration Records for High Voltage Rig',
    ],
  },
  {
    standardCode: 'IS 16046 (Part 2) : 2018',
    standardTitle: 'Secondary Lithium Cells and Batteries for Portable Applications',
    category: 'Electronics & IT Products',
    scheme: 'MeitY Compulsory Registration Scheme (CRS)',
    division: 'Batteries & Energy Storage (LITD 10)',
    scopeSummary: 'Continuous charging endurance, external short-circuit protection at 55°C, and 130°C thermal abuse containment without explosion.',
    checklist: [
      'External Short-Circuit Test Report',
      'Thermal Abuse & Drop Test (1.0m)',
      'Cell UN 38.3 Transportation Compliance',
      'Factory Quality Plan for Cell Balancing',
    ],
  },
  {
    standardCode: 'IS 13252 (Part 1) / IS 16333',
    standardTitle: 'Information Technology Equipment Safety & Indian Language Support for Mobile Handsets',
    category: 'Electronics & IT Products',
    scheme: 'MeitY Compulsory Registration Scheme (CRS)',
    division: 'Electronics & IT Division (LITD 06)',
    scopeSummary: 'Specific Absorption Rate (SAR ≤ 1.6 W/kg), 22 official Indian scheduled language font display, and charger electrical safety.',
    checklist: [
      'SAR Lab Test Report from NABL Lab',
      'Indian Language Script Verification Certificate',
      'AC Power Adapter Test Report (IS 13252)',
      'IMEI TAC Certificate from DoT',
    ],
  },
  {
    standardCode: 'IS 13252 (Part 1) : 2010',
    standardTitle: 'Information Technology Equipment — Safety — General Requirements',
    category: 'Electronics & IT Products',
    scheme: 'MeitY Compulsory Registration Scheme (CRS)',
    division: 'Electronics & IT Division (LITD 06)',
    scopeSummary: 'Protective earthing impedance, touch leakage current (< 0.25mA), and power supply casing flammability rating (UL94 V-0).',
    checklist: [
      'Electrical Shock Protection Report',
      'Battery Safety Certificate (IS 16046 Part 2)',
      'SMPS Power Supply Test Report',
      'Factory DIC / Registration Deed',
    ],
  },
  {
    standardCode: 'IS 616 : 2017 / IEC 60065',
    standardTitle: 'Audio, Video and Similar Electronic Apparatus — Safety Requirements',
    category: 'Consumer Electronics',
    scheme: 'MeitY Compulsory Registration Scheme (CRS)',
    division: 'Audio Video Electronics (LITD 07)',
    scopeSummary: 'Dielectric strength test (4000V AC surge), sound pressure acoustic hazard limitation, and display enclosure flame retardance.',
    checklist: [
      'High-Voltage Flash Test Report',
      'Audio Acoustic Pressure Safety Report',
      'Flame Retardancy Test of Back Cover',
      'Factory Production Line High-Pot Test Log',
    ],
  },
  {
    standardCode: 'IS 2082 : 2018 / IS 302',
    standardTitle: 'Stationary Storage Type Electric Water Heaters — Safety & Efficiency',
    category: 'Household Electrical Appliances',
    scheme: 'Mandatory ISI Mark Scheme — Quality Control Order',
    division: 'Household Appliances (ETD 32)',
    scopeSummary: 'Hydrostatic tank pressure burst test (1.0 MPa), non-self-resetting thermal cut-out trip (< 95°C), and standing heat loss (kWh/24h).',
    checklist: [
      'Hydrostatic Pressure Burst Test Report',
      'Thermal Cut-Out & Thermostat Test',
      'Corrosion Resistance Inner Tank Report',
      'Standing Energy Loss Verification',
    ],
  },
  {
    standardCode: 'IS 1391 (Part 1 & 2) : 2017',
    standardTitle: 'Room Air Conditioners — Specification for Split and Unitary Systems',
    category: 'Household Electrical Appliances',
    scheme: 'DPIIT Quality Control Order & BEE Star Rating',
    division: 'Refrigeration & AC Division (MED 03)',
    scopeSummary: 'Calorimeter cooling capacity test, maximum operating pressure containment, and eco-friendly refrigerant leakage detection.',
    checklist: [
      'Calorimeter Room Cooling Capacity Report',
      'High Pressure Gas Line Burst Test',
      'BEE Star Labeling Test Dossier',
      'Refrigerant Leakage Alarm Inspection',
    ],
  },
  {
    standardCode: 'IS 17550 (Part 1) : 2021',
    standardTitle: 'Household Refrigerating Appliances — Characteristics and Test Methods',
    category: 'Household Electrical Appliances',
    scheme: 'DPIIT Quality Control Order',
    division: 'Refrigeration & AC Division (MED 03)',
    scopeSummary: 'Pull-down temperature cycling, storage temperature stability in freezer (-18°C), and magnetic door gasket hermetic sealing.',
    checklist: [
      'Pull-down Temperature Cycling Report',
      'Door Gasket Magnetic Seal Durability',
      'Flammable Refrigerant Isobutane (R600a) Safety',
      'Energy Consumption Pull-Down Test',
    ],
  },
  {
    standardCode: 'IS 4151 : 2020',
    standardTitle: 'Protective Helmets for Two-Wheeler Riders — Specification',
    category: 'Automotive & Road Safety',
    scheme: 'MoRTH Mandatory ISI Certification Scheme',
    division: 'Transport Engineering (TED 18)',
    scopeSummary: 'Impact attenuation against hemispherical and flat anvils, chinstrap retention dynamic extension, and visor optical clarity.',
    checklist: [
      'Impact Attenuation Test Report (NABL Lab)',
      'Chinstrap Dynamic Extension & Slippage Report',
      'Visor Scratch Resistance & Light Transmittance',
      'Factory Batch Helmet Testing Protocol',
    ],
  },
  {
    standardCode: 'IS 9873 (Part 1) : 2019',
    standardTitle: 'Safety of Toys — Mechanical and Physical Properties & Electric Safety',
    category: 'Consumer Goods & Toys',
    scheme: 'DPIIT Toys (Quality Control) Order',
    division: 'Consumer Products (CPD 24)',
    scopeSummary: 'Small parts choking hazard cylinder gauge, sharp edge assessment, and migration of toxic heavy metals (lead, cadmium, mercury).',
    checklist: [
      'Small Parts Choking Risk Lab Certificate',
      'Heavy Metals Toxicological Migration Report',
      'Electric Toy Battery Compartment Interlock',
      'BIS Scheme of Inspection and Testing (SIT)',
    ],
  },
  {
    standardCode: 'IS 16102 (Part 1) : 2012',
    standardTitle: 'Self-Ballasted LED-Lamps for General Lighting Services — Safety Requirements',
    category: 'Lighting & Electrotechnical',
    scheme: 'Compulsory Registration Scheme (CRS)',
    division: 'Electrotechnical Division (ETD 23)',
    scopeSummary: 'Photobiological safety (RG0/RG1 blue light hazard), cap retention torque test (3.0 Nm), and 4000V AC dielectric breakdown.',
    checklist: [
      'NABL Accredited Safety Test Report (IS 16102 Part 1)',
      'Photobiological Blue Light Safety Certificate',
      'Cap Torque Retention Test Certificate',
      'Quality Assurance Plan (QAP) for SMD Assembly',
    ],
  },
];

export const detectProductStandard = (productName: string, category: string = ''): DetectedStandard => {
  const combined = `${productName} ${category}`.toLowerCase();

  if (combined.includes('solar') || combined.includes('photovoltaic') || combined.includes('grid tie')) {
    return BIS_STANDARDS_CATALOG[0];
  }
  if (combined.includes('fan') || combined.includes('bldc')) {
    return BIS_STANDARDS_CATALOG[1];
  }
  if (combined.includes('plug') || combined.includes('socket') || combined.includes('smart plug') || combined.includes('smart switch')) {
    return BIS_STANDARDS_CATALOG[2];
  }
  if (combined.includes('battery') || combined.includes('power bank') || combined.includes('cell') || combined.includes('lithium')) {
    return BIS_STANDARDS_CATALOG[3];
  }
  if (combined.includes('mobile') || combined.includes('smartphone') || combined.includes('phone') || combined.includes('handset')) {
    return BIS_STANDARDS_CATALOG[4];
  }
  if (combined.includes('laptop') || combined.includes('notebook') || combined.includes('tablet') || combined.includes('computer') || combined.includes('pc')) {
    return BIS_STANDARDS_CATALOG[5];
  }
  if (combined.includes('adapter') || combined.includes('charger') || combined.includes('fast charger') || combined.includes('smps') || combined.includes('power supply')) {
    return BIS_STANDARDS_CATALOG[5];
  }
  if (combined.includes('tv') || combined.includes('television') || combined.includes('display') || combined.includes('monitor')) {
    return BIS_STANDARDS_CATALOG[6];
  }
  if (combined.includes('water heater') || combined.includes('geyser') || combined.includes('immersion')) {
    return BIS_STANDARDS_CATALOG[7];
  }
  if (combined.includes('air conditioner') || combined.includes('ac unit') || combined.includes('split ac')) {
    return BIS_STANDARDS_CATALOG[8];
  }
  if (combined.includes('refrigerator') || combined.includes('fridge') || combined.includes('freezer')) {
    return BIS_STANDARDS_CATALOG[9];
  }
  if (combined.includes('helmet')) {
    return BIS_STANDARDS_CATALOG[10];
  }
  if (combined.includes('toy') || combined.includes('game') || combined.includes('doll')) {
    return BIS_STANDARDS_CATALOG[11];
  }
  if (combined.includes('led') || combined.includes('bulb') || combined.includes('lamp') || combined.includes('lighting') || combined.includes('light')) {
    return BIS_STANDARDS_CATALOG[12];
  }

  // Fallback by category
  const catLower = category.toLowerCase();
  if (catLower.includes('solar') || catLower.includes('renewable')) return BIS_STANDARDS_CATALOG[0];
  if (catLower.includes('smart') || catLower.includes('iot')) return BIS_STANDARDS_CATALOG[2];
  if (catLower.includes('household')) return BIS_STANDARDS_CATALOG[1];
  if (catLower.includes('lighting')) return BIS_STANDARDS_CATALOG[12];
  if (catLower.includes('electronic') || catLower.includes('it')) return BIS_STANDARDS_CATALOG[5];

  // Generic fallback
  return {
    standardCode: 'IS 13252 (Part 1) / IS 302',
    standardTitle: 'General Electronic & Electrical Safety Specification',
    category: category || 'General Equipment',
    scheme: 'BIS Scheme of Inspection & Certification',
    division: 'Bureau of Indian Standards Central Committee',
    scopeSummary: 'General dielectric insulation, creepage distances, and protection against electrical shock.',
    checklist: [
      'Product Technical Data Sheet',
      'Accredited Laboratory Safety Test Report',
      'Factory Quality Assurance Manual',
      'Manufacturer Incorporation Proof',
    ],
  };
};
