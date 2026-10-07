<?php

namespace App\Http\Controllers;

use App\Models\Product;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class CatalogController extends Controller
{
    private function query()
    {
        return Product::query()->with(['category', 'variants', 'images']);
    }

    public function index(Request $request): JsonResponse
    {
        $params = $request->validate([
            'skip' => ['sometimes', 'integer', 'min:0'],
            'limit' => ['sometimes', 'integer', 'min:1', 'max:100'],
        ]);
        $products = $this->query()->where('is_active', true)
            ->skip($params['skip'] ?? 0)->take($params['limit'] ?? 20)->get();

        return response()->json($products);
    }

    public function show(int $product_id): JsonResponse
    {
        $product = $this->query()->find($product_id);
        if (! $product) {
            return response()->json(['detail' => 'Product not found'], 404);
        }

        return response()->json($product);
    }
}
