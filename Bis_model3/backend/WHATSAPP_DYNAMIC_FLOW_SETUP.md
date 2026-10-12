# ISense Dynamic WhatsApp Flow setup

This patch adds a Meta encrypted data-exchange endpoint and a custom Flow definition with product-specific screens for water bottles/flasks, backpacks/bags, RC cars/toys, and a general fallback.

## 1. Install dependency and generate encryption keys

From the backend folder:

```powershell
python -m pip install -r requirements.txt
python generate_flow_keys.py
```

Keep `whatsapp_flow_private.pem` secret and out of Git. Configure `WHATSAPP_FLOW_PRIVATE_KEY_PATH` to its absolute path in `.env`, for example `E:\BIS\BIS_model3\Bis_model3\backend\secrets\whatsapp_flow_private.pem`.

## 2. Deploy a public HTTPS endpoint

The endpoint is `POST https://YOUR_PUBLIC_HOST/api/whatsapp/flow`. It must be reachable from Meta over HTTPS and return within Meta's timeout. Localhost is not reachable by Meta. For development, keep your ngrok tunnel running and use its current HTTPS URL; for production, use a stable HTTPS host.

## 3. Register the public key with Meta

Use the exact WhatsApp **Phone Number ID** that will send the Flow. In Postman, send `POST https://graph.facebook.com/v22.0/PHONE_NUMBER_ID/whatsapp_business_encryption` with `Authorization: Bearer YOUR_ACCESS_TOKEN` and form field `business_public_key` containing the complete contents of `secrets/whatsapp_flow_public.pem`. Then call `GET https://graph.facebook.com/v22.0/PHONE_NUMBER_ID/whatsapp_business_encryption` and confirm the public key is registered. The access token needs the appropriate WhatsApp permissions. Never upload or share the private key or token.

## 4. Create the custom Flow (do not use a loan template)

The custom definition is `whatsapp_flows/isense_dynamic_product_flow.json`. Use Postman with Bearer-token authorization:

1. `POST https://graph.facebook.com/v22.0/WABA_ID/flows` as form-data: `name=ISense Dynamic Product Intake`, `categories=["CUSTOMER_SUPPORT"]`, and `endpoint_uri=https://YOUR_PUBLIC_HOST/api/whatsapp/flow`. Save the returned `id` as `FLOW_ID`.
2. `POST https://graph.facebook.com/v22.0/FLOW_ID/assets` as form-data with `file` set to `isense_dynamic_product_flow.json`, `name=flow.json`, and `asset_type=FLOW_JSON`.
3. Inspect `validation_errors` in the upload response. Fix every error before publishing.
4. `GET https://graph.facebook.com/v22.0/FLOW_ID?fields=id,name,status,validation_errors,data_api_version,data_channel_uri` and verify the endpoint URL and data API version.
5. Only after the endpoint is public, encryption key is registered, and validation passes, call `POST https://graph.facebook.com/v22.0/FLOW_ID/publish`. Publishing is not reversible; make a draft/test first.

Meta's current API collection documents these operations. Do not paste access tokens into chat or source code.

## 5. Configure the Flow ID

Set `WHATSAPP_PRODUCT_INTAKE_FLOW_ID=<published_flow_id>` in `.env`, restart FastAPI, then send a product-only WhatsApp message. `send_product_intake_flow` already passes the product name into the `PRODUCT_ROUTER` screen.

## 6. Test

- `POST /api/whatsapp/flow` is the encrypted endpoint; it is not a browser page and cannot be tested with a plain GET.
- Meta sends an encrypted `INIT` / `data_exchange` request; the handler decrypts it, selects a product screen, encrypts the response, and returns base64 text.
- Submit the Flow and confirm the normal WhatsApp webhook receives `interactive.nfm_reply.response_json` and passes the product answers into RAG.
- Test water bottle, backpack, RC car, and an unknown product.

## Limitations and safety

- The endpoint chooses among screens defined in the Flow JSON; it cannot invent new UI components at runtime. To add a new product family, add a screen and a route in `choose_product_screen` and `routing_model`.
- Product answers are user input, not regulatory evidence. The RAG engine must confirm applicability against current official BIS/QCO sources and state uncertainty when evidence is insufficient.
- The current endpoint validates Meta's HMAC signature when `WHATSAPP_APP_SECRET` is configured, but production deployment should also validate each `flow_token` against an active session and test signature behaviour with your attached Meta app.
- This patch is syntax-tested only; it has not been validated against your live Meta WABA. Meta schema validation, public endpoint reachability, public-key registration, and actual Flow delivery must be tested in your account.
