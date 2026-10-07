<?php

use Illuminate\Support\Facades\Route;

Route::get('/', fn () => response()->json(['message' => 'Sneaker Shop API']));
Route::get('/health', fn () => response()->json(['status' => 'ok', 'message' => 'Backend is running']));
