# FAHAMU SHAMBA - CALLING GUIDE

## Important

This guide is only valid after:

1. The IVR service is deployed and reachable over public HTTPS
2. Twilio webhooks are configured to that public endpoint
3. The Twilio number is active and tested

Do not treat the phone flow as production-ready until those checks are complete.

## Current Twilio Number

`+1 (320) 431-3553`

## Kenya Calling Format

Use:

```text
+13204313553
```

If the `+` prefix does not work on a device, use the carrier-supported international dialing prefix instead.

## Expected IVR Flow

1. Welcome message
2. Language selection
3. Crop, weather, or market option
4. Voice response from the service

## Production Notes

1. Twilio must call a public HTTPS webhook, not `localhost`
2. If you use ngrok for testing, that is only for staging, not long-term production
3. Audio prompts, keypad routing, and SMS follow-ups should be tested end-to-end before launch

## Support Checklist

Before publishing this number to users:

1. Confirm the IVR endpoint is live
2. Place a real inbound call
3. Verify language selection works
4. Verify a full recommendation flow works
5. Verify the fallback error prompt is understandable
