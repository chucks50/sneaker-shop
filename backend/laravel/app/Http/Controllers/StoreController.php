<?php

namespace App\Http\Controllers;

use App\Models\Address;
use App\Models\CartItem;
use App\Models\Order;
use App\Models\OrderItem;
use App\Models\Product;
use App\Models\ProductVariant;
use App\Models\User;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Stripe\Checkout\Session as StripeSession;
use Stripe\Exception\ApiErrorException;
use Stripe\Stripe;
use Stripe\Webhook;

class StoreController extends Controller
{
    private function user(Request $request): User
    {
        return $request->attributes->get('current_user');
    }

    public function addresses(Request $request): JsonResponse
    {
        return response()->json(Address::query()->where('user_id', $this->user($request)->id)->get());
    }

    public function createAddress(Request $request): JsonResponse
    {
        $data = $request->validate([
            'street' => ['required', 'string', 'max:255'],
            'city' => ['required', 'string', 'max:100'],
            'postal_code' => ['required', 'string', 'max:20'],
            'country' => ['required', 'string', 'max:100'],
        ]);
        $address = Address::query()->create($data + [
            'user_id' => $this->user($request)->id,
            'is_default' => false,
        ]);

        return response()->json($address);
    }

    public function cart(Request $request): JsonResponse
    {
        return response()->json(CartItem::query()->where('user_id', $this->user($request)->id)->get());
    }

    public function addCartItem(Request $request): JsonResponse
    {
        $data = $request->validate([
            'product_id' => ['required', 'integer', 'min:1'],
            'variant_id' => ['required', 'integer', 'min:1'],
            'quantity' => ['sometimes', 'integer', 'min:1'],
        ]);
        $quantity = $data['quantity'] ?? 1;
        $product = Product::query()->where('is_active', true)->find($data['product_id']);
        if (! $product) {
            return response()->json(['detail' => 'Product not found'], 404);
        }
        $variant = ProductVariant::query()->where('product_id', $product->id)->find($data['variant_id']);
        if (! $variant) {
            return response()->json(['detail' => 'Product variant not found'], 404);
        }

        $userId = $this->user($request)->id;
        $item = DB::transaction(function () use ($userId, $product, $variant, $quantity) {
            $lockedVariant = ProductVariant::query()->whereKey($variant->id)->lockForUpdate()->first();
            $item = CartItem::query()->where('user_id', $userId)->where('product_id', $product->id)
                ->where('variant_id', $variant->id)->lockForUpdate()->first();
            $newQuantity = $quantity + (int) ($item?->quantity ?? 0);
            if ($newQuantity > (int) $lockedVariant->stock_quantity) {
                return null;
            }
            if ($item) {
                $item->quantity = $newQuantity;
                $item->save();

                return $item;
            }

            return CartItem::query()->create([
                'user_id' => $userId, 'product_id' => $product->id,
                'variant_id' => $variant->id, 'quantity' => $quantity,
            ]);
        });

        if (! $item) {
            return response()->json(['detail' => 'Not enough stock available'], 400);
        }

        return response()->json($item);
    }

    public function updateCartItem(Request $request, int $item_id): JsonResponse
    {
        $data = $request->validate(['quantity' => ['required', 'integer', 'min:1']]);
        $item = CartItem::query()->where('user_id', $this->user($request)->id)->find($item_id);
        if (! $item) {
            return response()->json(['detail' => 'Cart item not found'], 404);
        }
        $variant = ProductVariant::query()->find($item->variant_id);
        if (! $variant || $data['quantity'] > (int) $variant->stock_quantity) {
            return response()->json(['detail' => 'Not enough stock available'], 400);
        }
        $item->quantity = $data['quantity'];
        $item->save();

        return response()->json($item);
    }

    public function removeCartItem(Request $request, int $item_id): JsonResponse
    {
        $item = CartItem::query()->where('user_id', $this->user($request)->id)->find($item_id);
        if (! $item) {
            return response()->json(['detail' => 'Cart item not found'], 404);
        }
        $item->delete();

        return response()->json(['detail' => 'Item removed from cart']);
    }

    public function createCheckoutSession(Request $request): JsonResponse
    {
        $data = $request->validate(['address_id' => ['required', 'integer', 'min:1']]);
        $user = $this->user($request);
        if (! config('services.stripe_secret')) {
            return response()->json(['detail' => 'Stripe is not configured'], 500);
        }
        $address = Address::query()->where('user_id', $user->id)->find($data['address_id']);
        if (! $address) {
            return response()->json(['detail' => 'Address not found'], 400);
        }

        $cartItems = CartItem::query()->where('user_id', $user->id)->get();
        if ($cartItems->isEmpty()) {
            return response()->json(['detail' => 'Cart is empty'], 400);
        }

        try {
            $order = DB::transaction(function () use ($cartItems, $user, $address) {
                $lines = [];
                $subtotal = 0.0;
                foreach ($cartItems as $cartItem) {
                    $product = Product::query()->where('is_active', true)->find($cartItem->product_id);
                    $variant = ProductVariant::query()->where('product_id', $cartItem->product_id)->find($cartItem->variant_id);
                    if (! $product) {
                        abort(response()->json(['detail' => 'Product '.$cartItem->product_id.' not found'], 404));
                    }
                    if (! $variant) {
                        abort(response()->json(['detail' => 'Variant '.$cartItem->variant_id.' not found'], 404));
                    }
                    $quantity = (int) $cartItem->quantity;
                    if ($quantity <= 0) {
                        abort(response()->json(['detail' => 'Invalid cart item quantity'], 400));
                    }
                    if ($quantity > (int) $variant->stock_quantity) {
                        abort(response()->json(['detail' => 'Not enough stock available'], 400));
                    }
                    $price = $variant->price_override ?? $product->base_price;
                    $subtotal += (float) $price * $quantity;
                    $lines[] = new OrderItem([
                        'product_id' => $product->id, 'variant_id' => $variant->id,
                        'quantity' => $quantity, 'unit_price' => $price,
                        'product_name_snapshot' => $product->name,
                    ]);
                }

                $order = Order::query()->create([
                    'user_id' => $user->id, 'address_id' => $address->id,
                    'status' => 'pending', 'payment_status' => 'pending',
                    'subtotal' => $subtotal, 'shipping_fee' => 0,
                    'total_amount' => $subtotal, 'payment_method' => 'stripe',
                    'created_at' => now(),
                ]);
                $order->items()->saveMany($lines);

                return $order->load('items');
            });

            Stripe::setApiKey(config('services.stripe_secret'));
            $lineItems = $order->items->map(fn (OrderItem $item) => [
                'price_data' => [
                    'currency' => config('services.stripe_currency', 'eur'),
                    'product_data' => ['name' => $item->product_name_snapshot],
                    'unit_amount' => (int) round($item->unit_price * 100),
                ],
                'quantity' => $item->quantity,
            ])->all();
            $params = [
                'mode' => 'payment',
                'line_items' => $lineItems,
                'success_url' => config('services.frontend_url').'/success?session_id={CHECKOUT_SESSION_ID}',
                'cancel_url' => config('services.frontend_url').'/cancel',
                'customer_email' => $user->email,
                'metadata' => ['order_id' => (string) $order->id, 'user_id' => (string) $user->id],
            ];
            if (config('services.stripe_payment_method_configuration')) {
                $params['payment_method_configuration'] = config('services.stripe_payment_method_configuration');
            }
            $session = StripeSession::create($params);
            $order->stripe_checkout_session_id = $session->id;
            $order->save();

            return response()->json([
                'order_id' => (int) $order->id,
                'session_id' => $session->id,
                'checkout_url' => $session->url,
                'payment_status' => $order->payment_status,
            ]);
        } catch (ApiErrorException $exception) {
            if (isset($order)) {
                $order->status = 'failed';
                $order->payment_status = 'failed';
                $order->save();
            }
            report($exception);

            return response()->json(['detail' => 'Stripe checkout failed: payment service unavailable'], 502);
        }
    }

    public function checkoutSessionStatus(Request $request): JsonResponse
    {
        $data = $request->validate(['session_id' => ['required', 'string', 'min:1']]);
        $user = $this->user($request);
        $order = Order::query()->where('user_id', $user->id)
            ->where('stripe_checkout_session_id', $data['session_id'])->first();
        if (! $order) {
            return response()->json(['detail' => 'Checkout session not found'], 404);
        }
        if (! config('services.stripe_secret')) {
            return response()->json(['detail' => 'Stripe is not configured'], 500);
        }
        try {
            Stripe::setApiKey(config('services.stripe_secret'));
            $session = StripeSession::retrieve($data['session_id']);
        } catch (ApiErrorException $exception) {
            report($exception);

            return response()->json(['detail' => 'Could not confirm payment with Stripe'], 502);
        }
        if (($session->metadata->order_id ?? null) != $order->id
            || ($session->metadata->user_id ?? null) != $user->id) {
            return response()->json(['detail' => 'Checkout session not found'], 404);
        }

        return response()->json([
            'order_id' => (int) $order->id,
            'payment_status' => $session->payment_status ?? 'unpaid',
        ]);
    }

    public function stripeWebhook(Request $request): JsonResponse
    {
        $secret = config('services.stripe_webhook_secret');
        if (! $secret) {
            return response()->json(['detail' => 'Stripe webhook secret is not configured'], 500);
        }
        try {
            $event = Webhook::constructEvent($request->getContent(), $request->header('stripe-signature', ''), $secret);
        } catch (\Throwable) {
            return response()->json(['detail' => 'Invalid Stripe webhook signature or payload'], 400);
        }

        $type = $event->type ?? '';
        $session = $event->data->object ?? null;
        if (! $session) {
            return response()->json(['received' => true]);
        }

        if (in_array($type, ['checkout.session.completed', 'checkout.session.async_payment_succeeded'], true)
            && ($session->payment_status ?? null) === 'paid') {
            $metadata = $session->metadata ?? (object) [];
            $orderId = (int) ($metadata->order_id ?? 0);
            $userId = (string) ($metadata->user_id ?? '');
            $result = DB::transaction(function () use ($session, $orderId, $userId) {
                $order = Order::query()->whereKey($orderId)->lockForUpdate()->first();
                if (! $order || (string) $order->user_id !== $userId) {
                    return ['detail' => 'Order not found', 'status' => 404];
                }
                if ($order->stripe_checkout_session_id !== $session->id) {
                    return ['detail' => 'Checkout session does not match order', 'status' => 400];
                }
                if ((int) $session->amount_total !== (int) round($order->total_amount * 100)
                    || strtolower((string) $session->currency) !== config('services.stripe_currency')) {
                    return ['detail' => 'Checkout amount or currency does not match order', 'status' => 400];
                }
                if ($order->payment_status !== 'paid') {
                    $order->status = 'paid';
                    $order->payment_status = 'paid';
                    $order->stripe_payment_intent_id = $session->payment_intent ?? null;
                    $order->save();
                    CartItem::query()->where('user_id', $order->user_id)->delete();
                }

                return null;
            });
            if ($result) {
                return response()->json(['detail' => $result['detail']], $result['status']);
            }
        }

        if (in_array($type, ['checkout.session.expired', 'checkout.session.async_payment_failed'], true)) {
            $metadata = $session->metadata ?? (object) [];
            Order::query()->whereKey((int) ($metadata->order_id ?? 0))
                ->where('user_id', (int) ($metadata->user_id ?? 0))
                ->where('stripe_checkout_session_id', $session->id)
                ->where('payment_status', '!=', 'paid')
                ->update(['status' => 'failed', 'payment_status' => 'failed']);
        }

        return response()->json(['received' => true]);
    }

    public function orders(Request $request): JsonResponse
    {
        $orders = Order::query()->with('items')->where('user_id', $this->user($request)->id)
            ->orderByDesc('created_at')->get();

        return response()->json($orders);
    }

    public function order(Request $request, int $order_id): JsonResponse
    {
        $order = Order::query()->with('items')->where('user_id', $this->user($request)->id)->find($order_id);
        if (! $order) {
            return response()->json(['detail' => 'Order not found'], 404);
        }

        return response()->json($order);
    }

    public function updateOrderStatus(Request $request, int $order_id): JsonResponse
    {
        $data = $request->validate([
            'status' => ['required', 'in:pending,paid,failed,cancelled,refunded,shipped'],
        ]);
        if ($data['status'] === 'paid') {
            return response()->json(['detail' => 'Payment status is controlled by Stripe'], 403);
        }
        $order = Order::query()->with('items')->find($order_id);
        if (! $order) {
            return response()->json(['detail' => 'Order not found'], 404);
        }
        $order->status = $data['status'];
        if (in_array($data['status'], ['failed', 'cancelled', 'refunded'], true)) {
            $order->payment_status = $data['status'];
        }
        $order->save();

        return response()->json($order->load('items'));
    }
}
