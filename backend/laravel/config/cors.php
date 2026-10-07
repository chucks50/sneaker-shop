<?php

$origins = array_filter(array_map('trim', explode(',', (string) env(
    'CORS_ALLOWED_ORIGINS',
    'https://sneaker-shop-ck.netlify.app'
))));

return [
    'paths' => ['api/*', 'health', 'up'],
    'allowed_methods' => ['*'],
    'allowed_origins' => array_values($origins),
    'allowed_origins_patterns' => [],
    'allowed_headers' => ['*'],
    'exposed_headers' => [],
    'max_age' => 0,
    'supports_credentials' => false,
];
