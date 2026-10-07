<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Relations\HasMany;

class User extends LegacyModel
{
    protected $table = 'users';

    protected $hidden = ['password_hash'];

    protected function casts(): array
    {
        return ['is_active' => 'boolean'];
    }

    public function addresses(): HasMany
    {
        return $this->hasMany(Address::class);
    }

    public function cartItems(): HasMany
    {
        return $this->hasMany(CartItem::class);
    }

    public function orders(): HasMany
    {
        return $this->hasMany(Order::class);
    }

    public function reviews(): HasMany
    {
        return $this->hasMany(Review::class);
    }
}
