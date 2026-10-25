# Third-party attribution and license inventory

Reviewed 25 October 2026. This is a component inventory for the current local synthetic portfolio, not a blanket legal compatibility certification. **MIT applies to original project material**; separate upstream terms and [preserved notices](../third_party/notices/README.md) remain applicable. See [scope/compatibility](LICENSING_STATUS.md).

## Reference material and original work

- [Akannione reference](https://github.com/Akannione/crm-sales-pipeline-automation-system): business/analytics inspiration only. No root LICENSE found during review; no code/data is authorized for copying on that basis. No copied material identified in LeadRevive.
- [Mohamed Bakaar reference](https://github.com/Bakaare/ai-lead-qualification-n8n/blob/main/LICENSE): MIT, copyright 2026 Mohamed Bakaar. Validation/deduplication concepts only; no workflow JSON/code copied. If substantial material is reused later, include its MIT copyright/permission notice.
- LeadRevive's synthetic data generator, SQL business rules, workflows, report narrative and application are project-authored with AI assistance. No reference project's business outcomes are claimed. Full research links and phase-specific origin records remain in [REFERENCES](REFERENCES.md).

## Direct Python dependencies

Versions are pinned by requirements.txt / requirements-dev.txt. Classifications were read from the installed pinned distributions; upstream LICENSE/COPYING files remain authoritative.

| Component | Version | License classification | Use |
|---|---|---|---|
| SQLAlchemy | 2.1.6 | MIT | Persistence |
| Alembic | 1.20.1 | MIT | Migrations |
| FastAPI | 0.162.0 | MIT | API |
| Uvicorn | 0.54.0 | BSD-3-Clause | Server |
| HTTPX | 0.28.1 | BSD-3-Clause | Local HTTP |
| python-multipart | 0.0.32 | Apache-2.0 | Upload parsing |
| psycopg / psycopg-binary | 3.3.4 | LGPL-3.0-only | PostgreSQL driver |
| openpyxl | 3.1.5 | MIT | Excel |
| python-pptx | 1.0.2 | MIT | Editable slides |
| python-docx | 1.2.0 | MIT | Editable report |
| ReportLab | 4.4.4 | BSD, upstream license.txt | Portable PDF |
| pypdf | 6.1.1 | BSD-3-Clause | Report verification |
| jsonschema | 4.25.1 | MIT | Optional schema validation |
| PyMuPDF | 1.26.5 | AGPL-3.0 / Artifex commercial alternative | Optional local PDF preview tooling; not server runtime |

LGPL is not MIT: retain the driver's license notices and follow applicable linking/distribution conditions when distributing software that includes it. PyMuPDF is not a permissive dependency: [upstream licensing](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright) describes AGPL and commercial alternatives. Merely declaring it as an optional development requirement does not settle every possible integration/distribution use case. No PyMuPDF binaries are bundled here; do not infer that all preview/binary distribution modes have been cleared.

## Frontend dependencies

frontend/package-lock.json records exact resolved versions, integrity and per-package license metadata. Direct components: React/react-dom **MIT**, lucide-react **ISC**, Vite/plugin-react **MIT**, Playwright **Apache-2.0**, axe-core/Playwright wrapper **MPL-2.0**. Transitive classifications in this lock include MIT, ISC, Apache-2.0, BSD-3-Clause, **MPL-2.0** and **CC-BY-4.0** (caniuse-lite). The frontend root package is original LeadRevive material under the root MIT license; it is not an unknown upstream dependency.

The source ZIP includes the lockfile, not node_modules or compiled frontend bundles. When redistributing a built application, preserve applicable notices; MPL obligations apply to covered files and CC-BY attribution applies to covered data. Do not replace all component licenses with the eventual project license. Installed package license files and lock metadata provide the version-specific inventory.

## Services, tools and product interfaces

| Component | Terms/source | Boundary |
|---|---|---|
| n8n 2.44.6 | [Sustainable Use License / enterprise exceptions](https://github.com/n8n-io/n8n/blob/master/LICENSE.md) | Separate self-hosted local service; original LeadRevive workflow JSON is not n8n source. Personal/noncommercial/internal-use permissions are restricted, not a blanket permissive license or hosted-resale authorization. |
| Mailpit 1.32.0 | [MIT](https://github.com/axllent/mailpit/blob/v1.32.0/LICENSE) | Local SMTP sink; no Mailpit source/image bundled |
| PostgreSQL 16 | [PostgreSQL License](https://www.postgresql.org/about/licence/) | Separate database image |
| Python / Node / container base OS | Respective runtime and OS package licenses | Docker pulls upstream images; source ZIP contains no image layers. A redistributed image needs its own notice inventory. |
| Power BI Desktop / Microsoft Office | Microsoft's product terms | User-installed proprietary tools, not redistributed. PBIX/PBIP and PPTX/DOCX are authored outputs, not tool installers. |

Screenshots are captures of the local synthetic project using these product interfaces; upstream marks/interface artwork remain their owners' material and imply no endorsement. No third-party stock imagery or copied customer data is used. Generated documents retain library-template metadata (including a default PPTX last-modifier name); it is not a project contributor attribution. Existing accepted artifacts/evidence are intentionally unchanged.

## Distribution rules for this candidate

Preserve this inventory and REFERENCES with the source. Do not bundle upstream code, images or binaries under a new project license without their notices. Recheck licenses when dependency versions or distribution scope changes. Public source publication, a hosted commercial service and redistribution of binary/image bundles are different scopes; this review covers the source-only local portfolio candidate.
