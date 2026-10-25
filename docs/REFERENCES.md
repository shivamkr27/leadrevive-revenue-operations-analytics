# Origin and attribution manifest

Current component classifications and distribution boundaries: [THIRD_PARTY_ATTRIBUTION.md](THIRD_PARTY_ATTRIBUTION.md). Original-project MIT scope and compatibility: [LICENSING_STATUS.md](LICENSING_STATUS.md). Upstream notice texts: [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md). Historical phase-specific review statements below retain their original dates.

Reviewed 24 October 2026. No third-party code, dataset, images or workflow JSON copied into LeadRevive.

| Source | Reviewed material | License / reuse decision |
|---|---|---|
| [Reference A](https://github.com/Akannione/crm-sales-pipeline-automation-system) | Repository tree, README, script excerpt, SQL queries, KPI sample output | GitHub license metadata null; no LICENSE in tree. Inspiration only, no code reuse. Its estimated win-probability model is not adopted. |
| [Reference B](https://github.com/Bakaare/ai-lead-qualification-n8n) | README, actual LICENSE, workflow node structure | MIT, copyright 2026 Mohamed Bakaar verified. Concept only: validate → duplicate branch → response. Original PostgreSQL-backed recovery workflow planned; no OpenAI/Sheets dependency. Any future code reuse requires MIT notice. |
| [n8n documentation](https://docs.n8n.io/) | Docker hosting documentation and reference links | Official integration source; verify current Compose/node instructions at Phase 3. No copied workflow. |
| [Send Email node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.sendemail/) | Required Phase 3 integration reference | Implementation review pending that phase. |
| [SMTP workflow example](https://n8n.io/workflows/7065-automate-personalized-email-campaigns-with-google-docs-sheets-and-smtp/) | Spec-provided reference | Not imported; deferred review until needed. |
| [Power BI Desktop](https://www.microsoft.com/en-us/download/details.aspx?id=58494) | Official download page | Required desktop tool, no local availability claim. |

Repository content can change; this records the inspection date and exact paths reviewed, not an immutable third-party release. LeadRevive data is generated from numbered fictional identities and project-authored rules. No reference-project business results are used as ours.

## Phase 2 official implementation references

- https://fastapi.tiangolo.com/tutorial/testing/ ? FastAPI test-client pattern.
- https://vite.dev/guide/ ? frontend build/development tool requirements.
- https://playwright.dev/docs/test-webserver ? browser suite lifecycle and isolated local server.

Reviewed during Phase 2. Implementation is original; no third-party application code copied. React, Vite, lucide-react, Playwright, axe, FastAPI and SQLAlchemy/Alembic are installed library dependencies under their own package licenses; dependency metadata/notices remain with distributions. The Sites skill was consulted for local-only interface/preview guidance, not hosted deployment.

## Phase 3 official implementation references

- https://docs.n8n.io/deploy/host-n8n/install-options/use-a-cloud-provider/use-docker-compose.md ? local Compose configuration and published stable version reviewed.
- https://docs.n8n.io/deploy/host-n8n/configure-n8n/use-the-command-line.md ? import/export/publish/unpublish commands; restart after CLI publishing.
- https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/ ? authenticated webhook and response behavior.
- https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/ ? HTTP credentials/body/retry integration.
- https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.scheduletrigger/ ? published schedule and timezone requirements.
- https://mailpit.axllent.org/docs/install/docker/ ? local SMTP/UI persistence and ports.
- https://mailpit.axllent.org/docs/usage/search-filters/ ? Message-ID reconciliation.
- https://mailpit.axllent.org/docs/integration/chaos/ ? real SMTP fault injection and restoration.
- https://github.com/axllent/mailpit/releases/tag/v1.32.0 ? pinned current release reviewed; local version verified.

Mailpit upstream v1.32.0 Chaos API schema was inspected to construct test requests. No Mailpit source code was copied. Four LeadRevive workflow JSON files and the zero-scope schedule test are original; exports contain credential references only. n8n/SQLAlchemy/Alembic/PostgreSQL/Mailpit/React libraries and images retain their own distribution licenses.
## Phase 5 document generation references

- https://python-pptx.readthedocs.io/en/latest/api/shapes.html — editable slide shapes, tables, pictures and native picture viewports.
- https://python-pptx.readthedocs.io/en/stable/api/slides.html — slide notes and presentation structure.
- https://python-docx.readthedocs.io/en/latest/api/document.html — editable document paragraphs, tables, pictures and save operations.

Phase 5 narrative, export validation, report templates and business calculations are project-authored. Installed library distributions retain their own dependency metadata/licenses. ReportLab supplies the portable PDF; optional local PyMuPDF rendering is a development-only review aid. No external model service or outbound mail provider is used by report generation.
