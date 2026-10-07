<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        if (! Schema::hasTable('users')) {
            Schema::create('users', function (Blueprint $t) {
                $t->increments('id');
                $t->string('email', 255)->unique()->index();
                $t->string('password_hash', 255);
                $t->string('first_name', 100);
                $t->string('last_name', 100);
                $t->string('phone', 50)->nullable();
                $t->boolean('is_active')->default(true)->nullable();
            });
        }
        if (! Schema::hasTable('categories')) {
            Schema::create('categories', function (Blueprint $t) {
                $t->increments('id');
                $t->string('name', 100);
                $t->string('slug', 120)->unique();
            });
        }
        if (! Schema::hasTable('addresses')) {
            Schema::create('addresses', function (Blueprint $t) {
                $t->increments('id');
                $t->integer('user_id');
                $t->string('street', 255);
                $t->string('city', 100);
                $t->string('postal_code', 20);
                $t->string('country', 100);
                $t->boolean('is_default')->default(false)->nullable();
                $t->foreign('user_id')->references('id')->on('users');
            });
        }
        if (! Schema::hasTable('products')) {
            Schema::create('products', function (Blueprint $t) {
                $t->increments('id');
                $t->string('name', 200);
                $t->string('slug', 200)->unique();
                $t->string('brand', 100);
                $t->text('description');
                $t->double('base_price');
                $t->integer('category_id');
                $t->boolean('featured')->default(false)->nullable();
                $t->boolean('is_active')->default(true)->nullable();
                $t->foreign('category_id')->references('id')->on('categories');
            });
        }
        if (! Schema::hasTable('product_variants')) {
            Schema::create('product_variants', function (Blueprint $t) {
                $t->increments('id');
                $t->integer('product_id');
                $t->string('size', 20);
                $t->string('color', 50);
                $t->string('sku', 100)->unique();
                $t->integer('stock_quantity')->default(0)->nullable();
                $t->double('price_override')->nullable();
                $t->foreign('product_id')->references('id')->on('products');
            });
        }
        if (! Schema::hasTable('product_images')) {
            Schema::create('product_images', function (Blueprint $t) {
                $t->increments('id');
                $t->integer('product_id');
                $t->string('url', 500);
                $t->string('alt_text', 200)->nullable();
                $t->boolean('is_primary')->default(false)->nullable();
                $t->foreign('product_id')->references('id')->on('products');
            });
        }
        if (! Schema::hasTable('reviews')) {
            Schema::create('reviews', function (Blueprint $t) {
                $t->increments('id');
                $t->integer('product_id');
                $t->integer('user_id');
                $t->integer('rating');
                $t->text('comment')->nullable();
                $t->timestamp('created_at');
                $t->foreign('product_id')->references('id')->on('products');
                $t->foreign('user_id')->references('id')->on('users');
            });
        }
        if (! Schema::hasTable('cart_items')) {
            Schema::create('cart_items', function (Blueprint $t) {
                $t->increments('id');
                $t->integer('user_id');
                $t->integer('product_id');
                $t->integer('variant_id');
                $t->integer('quantity')->default(1);
                $t->foreign('user_id')->references('id')->on('users');
                $t->foreign('product_id')->references('id')->on('products');
                $t->foreign('variant_id')->references('id')->on('product_variants');
            });
        }
        if (! Schema::hasTable('orders')) {
            Schema::create('orders', function (Blueprint $t) {
                $t->increments('id');
                $t->integer('user_id');
                $t->integer('address_id');
                $t->string('status', 50)->default('pending');
                $t->string('payment_status', 50)->default('pending');
                $t->double('subtotal');
                $t->double('shipping_fee')->default(0);
                $t->double('total_amount');
                $t->string('payment_method', 50);
                $t->string('stripe_checkout_session_id', 255)->nullable()->unique();
                $t->string('stripe_payment_intent_id', 255)->nullable();
                $t->timestamp('created_at');
                $t->foreign('user_id')->references('id')->on('users');
                $t->foreign('address_id')->references('id')->on('addresses');
            });
        }
        if (! Schema::hasTable('order_items')) {
            Schema::create('order_items', function (Blueprint $t) {
                $t->increments('id');
                $t->integer('order_id');
                $t->integer('product_id');
                $t->integer('variant_id');
                $t->integer('quantity');
                $t->double('unit_price');
                $t->string('product_name_snapshot', 200);
                $t->foreign('order_id')->references('id')->on('orders');
                $t->foreign('product_id')->references('id')->on('products');
                $t->foreign('variant_id')->references('id')->on('product_variants');
            });
        }
    }

    public function down(): void
    {
        // Intentionally non-destructive: these tables may contain the existing store's production data.
    }
};
