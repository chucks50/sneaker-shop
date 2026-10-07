<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Relations\HasMany;

class Category extends LegacyModel
{
    protected $table = 'categories';

    public function products(): HasMany
    {
        return $this->hasMany(Product::class);
    }
}
