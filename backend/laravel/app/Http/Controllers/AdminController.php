<?php

namespace App\Http\Controllers;

use App\Models\CartItem;
use App\Models\Category;
use App\Models\OrderItem;
use App\Models\Product;
use App\Models\ProductImage;
use App\Models\ProductVariant;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;
use Illuminate\Validation\Rule;

class AdminController extends Controller
{
    private function productQuery()
    {
        return Product::query()->with(['category', 'variants', 'images']);
    }

    public function index(): JsonResponse
    {
        return response()->json($this->productQuery()->limit(100)->get());
    }

    public function create(Request $request): JsonResponse
    {
        $data = $request->validate([
            'name' => ['required', 'string', 'max:200'],
            'slug' => ['required', 'string', 'max:200', 'unique:products,slug'],
            'brand' => ['required', 'string', 'max:100'],
            'description' => ['required', 'string'],
            'base_price' => ['required', 'numeric', 'min:0'],
            'category_slug' => ['sometimes', 'string'],
            'image_url' => ['sometimes', 'string', 'max:500'],
            'featured' => ['sometimes', 'boolean'],
            'variants' => ['sometimes', 'array'],
            'variants.*.size' => ['required', 'string', 'max:20'],
            'variants.*.color' => ['required', 'string', 'max:50'],
            'variants.*.stock_quantity' => ['sometimes', 'integer', 'min:0'],
            'variants.*.price_override' => ['nullable', 'numeric', 'min:0'],
        ]);
        $category = Category::query()->where('slug', $data['category_slug'] ?? 'lifestyle')->first();
        if (! $category) {
            return response()->json(['detail' => 'Category not found'], 400);
        }

        $product = DB::transaction(function () use ($data, $category) {
            $product = Product::query()->create([
                'name' => $data['name'], 'slug' => $data['slug'], 'brand' => $data['brand'],
                'description' => $data['description'], 'base_price' => $data['base_price'],
                'category_id' => $category->id, 'featured' => $data['featured'] ?? false, 'is_active' => true,
            ]);
            $variants = $data['variants'] ?? [[
                'size' => '42', 'color' => 'Black / White', 'stock_quantity' => 0, 'price_override' => null,
            ]];
            foreach ($variants as $index => $variant) {
                ProductVariant::query()->create([
                    'product_id' => $product->id,
                    'size' => $variant['size'], 'color' => $variant['color'],
                    'sku' => $this->uniqueSku($data['slug'], $variant['size'], $index),
                    'stock_quantity' => $variant['stock_quantity'] ?? 0,
                    'price_override' => $variant['price_override'] ?? null,
                ]);
            }
            if (! empty($data['image_url'])) {
                ProductImage::query()->create([
                    'product_id' => $product->id, 'url' => $data['image_url'],
                    'alt_text' => $data['name'], 'is_primary' => true,
                ]);
            }

            return $product;
        });

        return response()->json($this->productQuery()->find($product->id));
    }

    public function update(Request $request, int $product_id): JsonResponse
    {
        $product = Product::query()->find($product_id);
        if (! $product) {
            return response()->json(['detail' => 'Product not found'], 404);
        }
        $data = $request->validate([
            'name' => ['sometimes', 'nullable', 'string', 'max:200'],
            'slug' => ['sometimes', 'nullable', 'string', 'max:200', Rule::unique('products', 'slug')->ignore($product_id)],
            'brand' => ['sometimes', 'nullable', 'string', 'max:100'],
            'description' => ['sometimes', 'nullable', 'string'],
            'base_price' => ['sometimes', 'nullable', 'numeric', 'min:0'],
            'category_slug' => ['sometimes', 'nullable', 'string'],
            'image_url' => ['sometimes', 'nullable', 'string', 'max:500'],
            'featured' => ['sometimes', 'nullable', 'boolean'],
            'is_active' => ['sometimes', 'nullable', 'boolean'],
            'variants' => ['sometimes', 'nullable', 'array'],
            'variants.*.size' => ['required_with:variants', 'string', 'max:20'],
            'variants.*.color' => ['required_with:variants', 'string', 'max:50'],
            'variants.*.stock_quantity' => ['sometimes', 'integer', 'min:0'],
            'variants.*.price_override' => ['nullable', 'numeric', 'min:0'],
        ]);
        $category = null;
        if (! empty($data['category_slug'])) {
            $category = Category::query()->where('slug', $data['category_slug'])->first();
            if (! $category) {
                return response()->json(['detail' => 'Category not found'], 400);
            }
        }

        DB::transaction(function () use ($product, $data, $category) {
            foreach (['name', 'slug', 'brand', 'description', 'base_price', 'featured', 'is_active'] as $field) {
                if (array_key_exists($field, $data) && $data[$field] !== null) {
                    $product->{$field} = $data[$field];
                }
            }
            if ($category) {
                $product->category_id = $category->id;
            }
            $product->save();

            if (array_key_exists('image_url', $data) && $data['image_url'] !== null) {
                $image = ProductImage::query()->where('product_id', $product->id)->where('is_primary', true)->first();
                if (! $image) {
                    $image = new ProductImage(['product_id' => $product->id, 'is_primary' => true]);
                }
                $image->url = $data['image_url'];
                $image->alt_text = $product->name;
                $image->save();
            }

            if (array_key_exists('variants', $data) && $data['variants'] !== null) {
                $keepIds = [];
                foreach ($data['variants'] as $index => $variantData) {
                    $variant = ProductVariant::query()->where('product_id', $product->id)
                        ->where('size', $variantData['size'])->where('color', $variantData['color'])->first();
                    if (! $variant) {
                        $variant = ProductVariant::query()->create([
                            'product_id' => $product->id,
                            'size' => $variantData['size'], 'color' => $variantData['color'],
                            'sku' => $this->uniqueSku($product->slug, $variantData['size'], $index),
                            'stock_quantity' => 0,
                        ]);
                    }
                    $variant->stock_quantity = $variantData['stock_quantity'] ?? $variant->stock_quantity;
                    $variant->price_override = $variantData['price_override'] ?? null;
                    $variant->save();
                    $keepIds[] = $variant->id;
                }

                $unused = ProductVariant::query()->where('product_id', $product->id)->whereNotIn('id', $keepIds)->get();
                foreach ($unused as $variant) {
                    $isReferenced = CartItem::query()->where('variant_id', $variant->id)->exists()
                        || OrderItem::query()->where('variant_id', $variant->id)->exists();
                    if ($isReferenced) {
                        $variant->stock_quantity = 0;
                        $variant->save();
                    } else {
                        $variant->delete();
                    }
                }
            }
        });

        return response()->json($this->productQuery()->find($product_id));
    }

    public function deactivate(int $product_id): JsonResponse
    {
        $product = $this->productQuery()->find($product_id);
        if (! $product) {
            return response()->json(['detail' => 'Product not found'], 404);
        }
        $product->is_active = false;
        $product->save();

        return response()->json($this->productQuery()->find($product_id));
    }

    private function uniqueSku(string $slug, string $size, int $index): string
    {
        $base = Str::slug($slug.'-'.$size.'-'.$index);
        $sku = substr($base, 0, 90);
        $suffix = 1;
        while (ProductVariant::query()->where('sku', $sku)->exists()) {
            $sku = substr($base, 0, 85).'-'.$suffix++;
        }

        return $sku;
    }
}
