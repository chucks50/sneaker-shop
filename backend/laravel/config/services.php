<?php

return [
    'legacy_jwt_secret' => env('JWT_SECRET_KEY'),
    'admin_email' => env('ADMIN_EMAIL', ''),
    'access_token_expire_minutes' => (int) env('ACCESS_TOKEN_EXPIRE_MINUTES', 30),
    'frontend_url' => rtrim(env('FRONTEND_URL', 'http://localhost:5173'), '/'),
    'stripe_secret' => env('STRIPE_SECRET_KEY'),
    'stripe_webhook_secret' => env('STRIPE_WEBHOOK_SECRET'),
    'stripe_currency' => strtolower(env('STRIPE_CURRENCY', 'eur')),
    'stripe_payment_method_configuration' => env('STRIPE_PAYMENT_METHOD_CONFIGURATION'),
];
