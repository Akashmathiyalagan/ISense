# ISense WhatsApp Flows integration patch

This patch adds a Meta WhatsApp Flow message for product intake and consumes the completed form through the existing `/api/webhook/whatsapp` webhook. It keeps the current RAG engine and WhatsApp message client.

## What it does

- When a user sends a short product description such as `water bottle`, `back bag`, or `I made a steel water bottle`, the backend sends the configured product-intake Flow inside WhatsApp.
- The Flow collects product name/type, material, capacity/specification, intended use, manufacturing origin, and requested BIS guidance.
- When the user submits the Flow, Meta sends an `interactive.nfm_reply` message to the existing webhook. The backend turns the answers into a user query and passes it to the existing conversational assistant/RAG pipeline.
- Regulatory answers still depend on the official documents currently indexed; questionnaire answers are user facts, not proof of legal applicability.

## Meta setup (required)

1. Open Meta for Developers / WhatsApp Manager for the same WABA used by the existing Cloud API integration.
2. Create a WhatsApp Flow named `ISense Product Intake` in the Flow Builder.
3. Import/build the JSON from `whatsapp_flows/isense_product_intake_flow.json` using the Flow Builder's supported JSON upload/editing workflow. Validate and publish it.
4. Copy the published Flow ID into backend `.env` as `WHATSAPP_PRODUCT_INTAKE_FLOW_ID=YOUR_PUBLISHED_FLOW_ID`.
5. Ensure `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN`, and webhook subscriptions are configured as before. Restart Uvicorn after editing `.env`.
6. Test from a WhatsApp client supported by Flows. Meta notes that Flows may not be delivered to unsupported WhatsApp versions.

This is a static universal intake Flow (no encrypted data-exchange endpoint is needed for this version). The product name is passed as initial screen data. Its fields are generic enough to cover different products; it does not dynamically change its list of fields per product. Truly different screen/option layouts generated at runtime require an endpoint-backed Flow and Meta's encrypted Flow data-exchange protocol.

## Environment variable

Add to `.env`:

```env
WHATSAPP_PRODUCT_INTAKE_FLOW_ID=
```

Do not paste API tokens into source files or share `.env`.

## Test sequence

1. Send `water bottle` to the business number. Expect a Flow message instead of the long RAG answer.
2. Submit the form. Expect the webhook to log that a product-intake Flow submission arrived and then return a grounded BIS answer based on the submitted details.
3. Repeat with `back bag` and `rc car`.
4. Send a direct regulatory question such as `What documents are needed for an RC car?`; this should continue through the normal RAG route.
5. If the Flow is not sent, check `/api/whatsapp/status` for `productIntakeFlowConfigured`, the server's current code path, and Meta API error logs (never log tokens).

## Limitations

- Meta Flow must be created and published in your own WABA; this patch cannot create it inside your Meta dashboard.
- This Flow is not an approval/certification form and does not submit an application to BIS.
- Product-specific legal requirements must be verified against the indexed official BIS/QCO/procedure evidence.
