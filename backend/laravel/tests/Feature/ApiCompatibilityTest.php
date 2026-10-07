<?php

namespace Tests\Feature;

use App\Models\Address;
use App\Models\Category;
use App\Models\Order;
use App\Models\Product;
use App\Models\ProductVariant;
use App\Services\TokenService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Testing\TestResponse;
use Stripe\ApiRequestor;
use Stripe\HttpClient\ClientInterface;
use Stripe\Stripe;
use Tests\TestCase;

class ApiCompatibilityTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();
        config([
            'services.legacy_jwt_secret' => str_repeat('t', 64),
            'services.admin_email' => 'admin@example.com',
            'services.stripe_secret' => null,
        ]);
    }

    public function test_public_paths_authentication_and_current_user_contract(): void
    {
        $this->getJson('/')->assertOk()->assertExactJson(['message' => 'Sneaker Shop API']);
        $this->getJson('/health')->assertOk()->assertExactJson([
            'status' => 'ok', 'message' => 'Backend is running',
        ]);
        $this->getJson('/api/products')->assertOk()->assertExactJson([]);

        $payload = [
            'first_name' => 'Alice', 'last_name' => 'Tester',
            'email' => 'alice@example.com', 'password' => 'secret123',
        ];
        $this->postJson('/api/auth/register', $payload)->assertOk()
            ->assertJsonStructure(['id', 'email', 'first_name', 'last_name', 'is_active'])
            ->assertJsonMissingPath('password_hash');
        $login = $this->postJson('/api/auth/login', [
            'email' => $payload['email'], 'password' => $payload['password'],
        ])->assertOk()->assertJsonStructure(['access_token', 'token_type', 'user'])->json();
        $this->getJson('/api/auth/me', ['Authorization' => 'Bearer '.$login['access_token']])
            ->assertOk()->assertJsonPath('email', $payload['email']);
        $this->getJson('/api/auth/me')->assertUnauthorized()->assertJsonPath('detail', 'Authentication required');
    }

    public function test_address_cart_and_admin_product_contracts(): void
    {
        $category = Category::query()->create(['name' => 'Running', 'slug' => 'running']);
        $product = Product::query()->create([
            'name' => 'Test Runner', 'slug' => 'test-runner', 'brand' => 'Test',
            'description' => 'Test shoe', 'base_price' => 89.99,
            'category_id' => $category->id, 'featured' => false, 'is_active' => true,
        ]);
        $variant = ProductVariant::query()->create([
            'product_id' => $product->id, 'size' => '42', 'color' => 'Blue',
            'sku' => 'test-runner-42', 'stock_quantity' => 5, 'price_override' => null,
        ]);
        $this->postJson('/api/auth/register', [
            'first_name' => 'Admin', 'last_name' => 'User',
            'email' => 'admin@example.com', 'password' => 'secret123',
        ])->assertOk();
        $token = $this->postJson('/api/auth/login', [
            'email' => 'admin@example.com', 'password' => 'secret123',
        ])->assertOk()->json('access_token');
        $headers = ['Authorization' => 'Bearer '.$token];

        $address = $this->postJson('/api/addresses', [
            'street' => 'Main Street 1', 'city' => 'Amsterdam',
            'postal_code' => '1000AA', 'country' => 'Netherlands',
        ], $headers)->assertOk()->assertJsonPath('user_id', 1)->json();
        $this->getJson('/api/addresses', $headers)->assertOk()->assertJsonCount(1);
        $item = $this->postJson('/api/cart/items', [
            'product_id' => $product->id, 'variant_id' => $variant->id, 'quantity' => 2,
        ], $headers)->assertOk()->assertJsonPath('quantity', 2)->json();
        $this->putJson('/api/cart/items/'.$item['id'], ['quantity' => 3], $headers)
            ->assertOk()->assertJsonPath('quantity', 3);
        $this->getJson('/api/cart', $headers)->assertOk()->assertJsonCount(1);
        $this->deleteJson('/api/cart/items/'.$item['id'], [], $headers)
            ->assertOk()->assertExactJson(['detail' => 'Item removed from cart']);
        $this->getJson('/api/admin/products', $headers)->assertOk()->assertJsonCount(1);
        $this->getJson('/api/orders', $headers)->assertOk()->assertExactJson([]);
        $this->getJson('/api/orders/999', $headers)->assertNotFound()
            ->assertJsonPath('detail', 'Order not found');
        $this->assertSame((int) $address['id'], (int) Address::query()->first()->id);
    }

    public function test_regular_users_cannot_access_admin_routes_and_cart_stock_is_enforced(): void
    {
        $category = Category::query()->create(['name' => 'Running', 'slug' => 'running']);
        $product = Product::query()->create([
            'name' => 'Test Runner', 'slug' => 'test-runner', 'brand' => 'Test',
            'description' => 'Test shoe', 'base_price' => 89.99,
            'category_id' => $category->id, 'featured' => false, 'is_active' => true,
        ]);
        $variant = ProductVariant::query()->create([
            'product_id' => $product->id, 'size' => '42', 'color' => 'Blue',
            'sku' => 'test-runner-42', 'stock_quantity' => 1,
        ]);
        $this->postJson('/api/auth/register', [
            'first_name' => 'Regular', 'last_name' => 'User',
            'email' => 'regular@example.com', 'password' => 'secret123',
        ])->assertOk();
        $token = $this->postJson('/api/auth/login', [
            'email' => 'regular@example.com', 'password' => 'secret123',
        ])->assertOk()->json('access_token');
        $headers = ['Authorization' => 'Bearer '.$token];
        $this->getJson('/api/admin/products', $headers)->assertForbidden()
            ->assertJsonPath('detail', 'Admin access required');
        $this->postJson('/api/cart/items', [
            'product_id' => $product->id, 'variant_id' => $variant->id, 'quantity' => 2,
        ], $headers)->assertStatus(400)->assertJsonPath('detail', 'Not enough stock available');
    }

    public function test_admin_can_create_update_and_soft_delete_a_product(): void
    {
        Category::query()->create(['name' => 'Running', 'slug' => 'running']);
        $this->postJson('/api/auth/register', [
            'first_name' => 'Admin', 'last_name' => 'User',
            'email' => 'admin@example.com', 'password' => 'secret123',
        ])->assertOk();
        $token = $this->postJson('/api/auth/login', [
            'email' => 'admin@example.com', 'password' => 'secret123',
        ])->assertOk()->json('access_token');
        $headers = ['Authorization' => 'Bearer '.$token];

        $created = $this->postJson('/api/admin/products', [
            'name' => 'Admin Runner', 'slug' => 'admin-runner', 'brand' => 'Test',
            'description' => 'Admin-created shoe', 'base_price' => 79.99,
            'category_slug' => 'running',
            'variants' => [['size' => '43', 'color' => 'Green', 'stock_quantity' => 4]],
        ], $headers)->assertOk()->assertJsonPath('base_price', 79.99)->json();
        $this->putJson('/api/admin/products/'.$created['id'], ['base_price' => 89.99], $headers)
            ->assertOk()->assertJsonPath('base_price', 89.99);
        $this->deleteJson('/api/admin/products/'.$created['id'], [], $headers)
            ->assertOk()->assertJsonPath('is_active', false);
        $this->getJson('/api/products')->assertOk()->assertJsonCount(0);
    }

    public function test_password_reset_and_invalid_stripe_webhook_contracts(): void
    {
        $this->postJson('/api/auth/register', [
            'first_name' => 'Reset', 'last_name' => 'User',
            'email' => 'reset@example.com', 'password' => 'secret123',
        ])->assertOk();
        $token = app(TokenService::class)->issueResetToken('reset@example.com');
        $this->postJson('/api/auth/reset-password', [
            'email' => 'reset@example.com', 'reset_token' => $token,
            'new_password' => 'newsecret456',
        ])->assertOk()->assertExactJson(['message' => 'Password updated successfully.']);
        $this->postJson('/api/auth/login', [
            'email' => 'reset@example.com', 'password' => 'newsecret456',
        ])->assertOk();

        config(['services.stripe_webhook_secret' => 'whsec_test_for_signature_check']);
        $this->call('POST', '/api/webhooks/stripe', [], [], [], [
            'CONTENT_TYPE' => 'application/json', 'HTTP_STRIPE_SIGNATURE' => 'invalid',
        ], '{}')->assertStatus(400)->assertJsonPath('detail', 'Invalid Stripe webhook signature or payload');
    }

    public function test_checkout_uses_database_prices_and_a_signed_success_webhook_marks_order_paid(): void
    {
        $fixture = $this->prepareCheckoutFixture('stripe-success@example.com');
        $secret = 'whsec_feature_test_secret';
        config([
            'services.stripe_secret' => 'sk_test_mock',
            'services.stripe_webhook_secret' => $secret,
        ]);
        $httpClient = new class implements ClientInterface
        {
            public array $requests = [];

            public array $metadata = [];

            public function request($method, $absUrl, $headers, $params, $hasFile, $apiMode = 'v1', $maxNetworkRetries = null): array
            {
                $this->requests[] = compact('method', 'absUrl', 'params');
                $this->metadata = $params['metadata'] ?? $this->metadata;

                return [
                    json_encode([
                        'id' => 'cs_test_laravel_checkout',
                        'object' => 'checkout.session',
                        'url' => 'https://checkout.stripe.com/cs_test_laravel_checkout',
                        'payment_status' => 'unpaid',
                        'metadata' => $this->metadata,
                    ], JSON_THROW_ON_ERROR),
                    200,
                    ['request-id' => 'req_test_laravel_checkout'],
                ];
            }
        };
        ApiRequestor::setHttpClient($httpClient);
        Stripe::setApiKey('sk_test_mock');

        try {
            $checkout = $this->postJson('/api/checkout/create-session', [
                'address_id' => $fixture['address_id'],
            ], $fixture['headers'])->assertOk()->json();
            $this->getJson('/api/checkout/session-status?session_id='.$checkout['session_id'], $fixture['headers'])
                ->assertOk()->assertJsonPath('payment_status', 'unpaid');
        } finally {
            ApiRequestor::setHttpClient(null);
            Stripe::setApiKey(null);
        }

        $this->assertSame(12345, $httpClient->requests[0]['params']['line_items'][0]['price_data']['unit_amount']);
        $this->assertSame('cs_test_laravel_checkout', $checkout['session_id']);
        $this->assertSame('https://checkout.stripe.com/cs_test_laravel_checkout', $checkout['checkout_url']);
        $order = Order::query()->with('items')->findOrFail($checkout['order_id']);
        $this->assertSame('pending', $order->payment_status);
        $this->assertSame(123.45, $order->items[0]->unit_price);

        $this->postSignedStripeEvent([
            'id' => 'cs_test_laravel_checkout',
            'object' => 'checkout.session',
            'payment_status' => 'paid',
            'payment_intent' => 'pi_test_laravel_checkout',
            'amount_total' => 12345,
            'currency' => 'eur',
            'metadata' => [
                'order_id' => (string) $order->id,
                'user_id' => (string) $order->user_id,
            ],
        ], 'checkout.session.completed', $secret)->assertOk()->assertExactJson(['received' => true]);
        $this->postSignedStripeEvent([
            'id' => 'cs_test_laravel_checkout',
            'object' => 'checkout.session',
            'payment_status' => 'paid',
            'payment_intent' => 'pi_test_laravel_checkout',
            'amount_total' => 12345,
            'currency' => 'eur',
            'metadata' => ['order_id' => (string) $order->id, 'user_id' => (string) $order->user_id],
        ], 'checkout.session.completed', $secret)->assertOk()->assertExactJson(['received' => true]);

        $order->refresh();
        $this->assertSame('paid', $order->payment_status);
        $this->assertSame('paid', $order->status);
        $this->assertSame('pi_test_laravel_checkout', $order->stripe_payment_intent_id);
        $this->getJson('/api/cart', $fixture['headers'])->assertOk()->assertJsonCount(0);
    }

    public function test_expired_checkout_marks_order_failed_and_keeps_the_cart(): void
    {
        $fixture = $this->prepareCheckoutFixture('stripe-expired@example.com');
        $secret = 'whsec_expired_feature_test';
        config([
            'services.stripe_secret' => 'sk_test_mock',
            'services.stripe_webhook_secret' => $secret,
        ]);
        ApiRequestor::setHttpClient(new class implements ClientInterface
        {
            public array $metadata = [];

            public function request($method, $absUrl, $headers, $params, $hasFile, $apiMode = 'v1', $maxNetworkRetries = null): array
            {
                $this->metadata = $params['metadata'] ?? $this->metadata;

                return [
                    json_encode([
                        'id' => 'cs_test_expired_checkout',
                        'object' => 'checkout.session',
                        'url' => 'https://checkout.stripe.com/cs_test_expired_checkout',
                        'payment_status' => 'unpaid',
                        'metadata' => $this->metadata,
                    ], JSON_THROW_ON_ERROR),
                    200,
                    ['request-id' => 'req_test_expired_checkout'],
                ];
            }
        });
        Stripe::setApiKey('sk_test_mock');

        try {
            $checkout = $this->postJson('/api/checkout/create-session', [
                'address_id' => $fixture['address_id'],
            ], $fixture['headers'])->assertOk()->json();
            $this->getJson('/api/checkout/session-status?session_id='.$checkout['session_id'], $fixture['headers'])
                ->assertOk()->assertJsonPath('payment_status', 'unpaid');
        } finally {
            ApiRequestor::setHttpClient(null);
            Stripe::setApiKey(null);
        }

        $order = Order::query()->findOrFail($checkout['order_id']);
        $this->postSignedStripeEvent([
            'id' => 'cs_test_expired_checkout',
            'object' => 'checkout.session',
            'payment_status' => 'unpaid',
            'metadata' => [
                'order_id' => (string) $order->id,
                'user_id' => (string) $order->user_id,
            ],
        ], 'checkout.session.expired', $secret)->assertOk()->assertExactJson(['received' => true]);

        $this->assertSame('failed', $order->fresh()->payment_status);
        $this->getJson('/api/cart', $fixture['headers'])->assertOk()->assertJsonCount(1);
    }

    private function prepareCheckoutFixture(string $email): array
    {
        $category = Category::query()->create(['name' => 'Running', 'slug' => 'running']);
        $product = Product::query()->create([
            'name' => 'Checkout Runner', 'slug' => 'checkout-runner', 'brand' => 'Test',
            'description' => 'Checkout test shoe', 'base_price' => 123.45,
            'category_id' => $category->id, 'featured' => false, 'is_active' => true,
        ]);
        $variant = ProductVariant::query()->create([
            'product_id' => $product->id, 'size' => '42', 'color' => 'Blue',
            'sku' => 'checkout-runner-42', 'stock_quantity' => 5,
            'price_override' => null,
        ]);
        $this->postJson('/api/auth/register', [
            'first_name' => 'Checkout', 'last_name' => 'User',
            'email' => $email, 'password' => 'secret123',
        ])->assertOk();
        $token = $this->postJson('/api/auth/login', [
            'email' => $email, 'password' => 'secret123',
        ])->assertOk()->json('access_token');
        $headers = ['Authorization' => 'Bearer '.$token];
        $address = $this->postJson('/api/addresses', [
            'street' => 'Market Street 7', 'city' => 'Amsterdam',
            'postal_code' => '1000AA', 'country' => 'Netherlands',
        ], $headers)->assertOk()->json();
        $this->postJson('/api/cart/items', [
            'product_id' => $product->id, 'variant_id' => $variant->id, 'quantity' => 1,
        ], $headers)->assertOk();

        return ['headers' => $headers, 'address_id' => $address['id']];
    }

    private function postSignedStripeEvent(array $session, string $type, string $secret): TestResponse
    {
        $payload = json_encode([
            'id' => 'evt_test_'.str_replace('.', '_', $type),
            'object' => 'event',
            'type' => $type,
            'data' => ['object' => $session],
        ], JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR);
        $timestamp = time();
        $signature = hash_hmac('sha256', $timestamp.'.'.$payload, $secret);

        return $this->call('POST', '/api/webhooks/stripe', [], [], [], [
            'CONTENT_TYPE' => 'application/json',
            'HTTP_STRIPE_SIGNATURE' => 't='.$timestamp.',v1='.$signature,
        ], $payload);
    }
}
