# PDF eSign

Desktop app to place signatures, names, dates, and images on PDFs and save a flattened signed copy.

## Features
- Open and preview PDF files
- Add overlays:
  - Typed signature (custom signature fonts)
  - Signature image
  - Name
  - Date
- Drag, resize, edit, and delete overlays before saving
- Save signed output as a new flattened PDF

## Tech Stack
- Python 3.11+
- PySide6 (UI)
- PyMuPDF / `fitz` (PDF rendering + save)

## Project Structure
```text
.
|-- main.py
|-- requirements.txt
|-- assets/
|   `-- fonts/
`-- app/
    |-- main_window.py
    |-- pdf_service.py
    |-- pdf_viewer.py
    |-- models.py
    |-- settings.py
    |-- tools.py
    |-- utils.py
    `-- image_service.py
```

## Setup
1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run
```bash
python main.py
```

## Usage
1. Click **Open PDF**.
2. Choose overlay type in the left panel.
3. Enter text or select image as needed.
4. Click **Place Overlay** and draw on the page.
5. Adjust overlay position/size if needed.
6. Click **Save As** to export signed PDF.

## Notes
- Signature fonts are loaded from `assets/fonts`.
- This app is local-only; no cloud upload is required.

## Legal Notice and Disclaimer
This project is provided for general document annotation and e-sign workflow support. It is not a law firm and does not provide legal advice. Use of this software does not create an attorney-client relationship.

### No Guarantee of Legal Enforceability
Whether an electronically signed document is legally enforceable depends on your jurisdiction, industry, document type, consent process, identity verification, record retention, and applicable laws (for example, ESIGN, UETA, eIDAS, or other local regulations). You are solely responsible for determining legal validity for your use case.

### User Responsibility
By using this software, you agree that you are responsible for:
- obtaining all required consents and disclosures;
- verifying signer identity where required;
- maintaining audit trails and records where required;
- complying with all applicable privacy, consumer, and electronic signature laws;
- verifying output accuracy before relying on any signed document.

### Security and Data Handling
- Files are processed locally on your machine by default.
- You are responsible for endpoint security, device access control, backup, malware protection, and secure storage/transmission of PDFs and signatures.
- Do not use this tool for regulated or high-risk workflows unless you have independently validated legal and technical compliance.

### Warranty Disclaimer
THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE, AND NON-INFRINGEMENT.

### Limitation of Liability
TO THE MAXIMUM EXTENT PERMITTED BY LAW, THE AUTHORS AND CONTRIBUTORS ARE NOT LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR EXEMPLARY DAMAGES, OR ANY LOSS OF DATA, REVENUE, PROFITS, OR BUSINESS OPPORTUNITY, ARISING FROM USE OF THE SOFTWARE.

### Third-Party Components
This project uses third-party libraries and fonts that are licensed separately. You are responsible for reviewing and complying with their license terms when distributing source code or executables.

### Release Guidance
Before shipping a desktop executable to users or customers, have your Terms of Use, Privacy Notice, and e-sign compliance flow reviewed by qualified counsel in each target jurisdiction.

## License
See [`LICENSE`](LICENSE) for the repository license.
