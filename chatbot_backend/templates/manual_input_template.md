# Manual Input Template
**Instructions**: Fill out each section completely. Text will be automatically chunked semantically. Do not trim content - the system will preserve everything. Include all sections.

## Document Metadata
- **Title**: Orbi Whole Home Tri-Band Mesh WiFi 6 System
- **Version**: v1.0
- **Source Type**: manual (options: manual, maintenance_guide, faq, troubleshooting, best_practices)
- **Language**: en-US
- **Author/Publisher**: NETGEAR, Inc

---

## Section 1: [Section Title]
- **Subtitle**: [Subsection if applicable]
- **Page Number**: [Page number in original document]
- **Section ID**: [Unique identifier, e.g., wired_connection_001]

### Content
[Full text content here - do not trim or summarize. Include all details, steps, specifications, warnings, etc. The system will automatically chunk this content while preserving everything.]

### Images
- **Image Filename**: startup_diagram.png
- **Firebase Path**: manual001/startup_diagram.png
- **Image Description**: [Detailed ALT text describing the image content]

### Metadata
- **Keywords**: [Comma-separated relevant terms]
- **Related Sections**: [List of related section IDs]
- **Is Complete Section**: [true/false - whether this stands alone]

## Section 2: Safety Procedures
- **Subtitle**: Pre-Installation & Operation Safety Check
- **Page Number**: 12
- **Section ID**: safety_procedures_001

### Content
Before installing or operating the Orbi Whole Home Tri-Band Mesh WiFi 6 System, complete the following safety and readiness checks to prevent damage to equipment and ensure reliable operation.

1 **Personal & Work Area Safety**
- Ensure dry hands when handling power adapters and Ethernet cables.
- Use a stable step stool or ladder if placing units on high shelves.
- Keep small parts (cable ties, rubber feet) away from children and pets.
- Avoid placing equipment where someone might trip on cables.

2 **Electrical & Power Considerations**
- Verify outlet voltage and frequency meet the power adapter specifications.
- Use only the supplied NETGEAR power adapters; do not use damaged cords.
- Consider a surge protector or UPS for the router and modem.
- Do not overload power strips; ensure adequate current capacity.

3 **Placement & Environment**
- Place the router near the modem in a centralized, ventilated area; avoid enclosed cabinets.
- Position the satellite mid-home, elevated on an open shelf; avoid metal cabinets, aquariums, and large appliances.
- Maintain clearance around vents for airflow; ambient operating temperature and humidity must meet the specifications in the manual.
- Keep units away from direct heat sources, liquids, and prolonged sunlight.

4 **RF & Interference Awareness**
-Maintain reasonable separation from microwave ovens, cordless phones, and Bluetooth hubs that may cause interference.
- Avoid stacking units directly on top of other wireless routers or access points.
- For best mesh performance, minimize dense obstacles (brick, concrete, metal lath).

5 **Cabling & Connectivity Checks**
- Inspect the modem's coax/ONT connection; confirm it is secure.
- Use a known-good Ethernet cable from modem LAN/ONT to the router Internet port.
- For wired backhaul, use Cat5e or better Ethernet from satellite to a LAN port on the router or switch.
- Label cables to simplify troubleshooting and future changes.

6 **Device Label & Credentials**
- Locate the SSID, WiFi password, admin URL (orbilogin.com), and QR code on the device labels.
- Record the serial numbers and MAC addresses of router and satellite for support and registration.
- Software & Firmware Readiness

7 **Install the NETGEAR Orbi app on a mobile device (iOS/Android).**
- Ensure the mobile device has Internet access (cellular) for account sign-in during initial setup if WiFi is not yet available.
- Check for the latest firmware after initial setup; update satellites first, then router.

**CRITICAL WARNING**: Do not block ventilation openings or operate the equipment with damaged power adapters or frayed cables. Do not perform a factory reset while firmware is updating. If LEDs indicate firmware corruption or repeated sync failures, disconnect power, verify cabling, and consult the Troubleshooting section.

**Environmental Considerations**:
- Ensure adequate ventilation and dust-free placement.
- If mounting near ceilings or in structured wiring panels, confirm ambient temperature remains within specified operating range.
- Plan satellite placement to avoid areas with high RF congestion (home theater racks, behind TVs).
- Confirm you have access to your ISP credentials (if PPPoE or static IP is required) before beginning setup.

### Images
- **Image Filename**: safety_checklist_diagram.png
- **Firebase Path**: manual001/safety_checklist_diagram.png
- **Image Description**: Diagram of recommended router and satellite placement with callouts for ventilation clearance, cable routing, surge protection, and label locations (SSID/password/QR code).

### Metadata
- **Keywords**: safety, installation, placement, ventilation, surge protector, RF interference, Ethernet, power adapter, firmware update
- **Related Sections**: [startup_procedures_001, maintenance_daily_001, emergency_procedures_001]
- **Is Complete Section**: true

## Section 3: [Next Section]
[Continue with additional sections...]

## Processing Instructions
- **Auto-chunking**: Enable semantic chunking with 30% overlap
- **Summary Generation**: Generate summaries for each chunk
- **Embedding**: Use text-embedding-004
- **Validation**: Check for unique IDs and sequential chunk ordering
- **Language Detection**: Verify language matches specified language code