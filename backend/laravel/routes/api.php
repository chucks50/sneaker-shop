<?php

use App\Http\Controllers\AdminController;
use App\Http\Controllers\AuthController;
use App\Http\Controllers\CatalogController;
use App\Http\Controllers\StoreController;
use Illuminate\Support\Facades\Route;

Route::get('/products', [CatalogController::class, 'index']);
Route::get('/products/{product_id}', [CatalogController::class, 'show'])->whereNumber('product_id');

Route::post('/auth/register', [AuthController::class, 'register']);
Route::post('/auth/login', [AuthController::class, 'login']);
Route::post('/auth/forgot-password', [AuthController::class, 'forgotPassword']);
Route::post('/auth/reset-password', [AuthController::class, 'resetPassword']);
Route::get('/auth/me', [AuthController::class, 'me'])->middleware('jwt');

Route::middleware('jwt')->group(function (): void {
    Route::get('/addresses', [StoreController::class, 'addresses']);
    Route::post('/addresses', [StoreController::class, 'createAddress']);
    Route::get('/cart', [StoreController::class, 'cart']);
    Route::post('/cart/items', [StoreController::class, 'addCartItem']);
    Route::put('/cart/items/{item_id}', [StoreController::class, 'updateCartItem'])->whereNumber('item_id');
    Route::delete('/cart/items/{item_id}', [StoreController::class, 'removeCartItem'])->whereNumber('item_id');
    Route::post('/checkout/create-session', [StoreController::class, 'createCheckoutSession']);
    Route::get('/checkout/session-status', [StoreController::class, 'checkoutSessionStatus']);
    Route::get('/orders', [StoreController::class, 'orders']);
    Route::get('/orders/{order_id}', [StoreController::class, 'order'])->whereNumber('order_id');
});

Route::post('/webhooks/stripe', [StoreController::class, 'stripeWebhook']);

Route::middleware(['jwt', 'admin'])->group(function (): void {
    Route::get('/admin/products', [AdminController::class, 'index']);
    Route::post('/admin/products', [AdminController::class, 'create']);
    Route::put('/admin/products/{product_id}', [AdminController::class, 'update'])->whereNumber('product_id');
    Route::delete('/admin/products/{product_id}', [AdminController::class, 'deactivate'])->whereNumber('product_id');
    Route::patch('/orders/{order_id}/status', [StoreController::class, 'updateOrderStatus'])->whereNumber('order_id');
});
