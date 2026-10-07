<?php

namespace App\Services;

use Firebase\JWT\JWT;
use Firebase\JWT\Key;
use RuntimeException;
use Throwable;

class TokenService
{
    private function secret(): string
    {
        $secret = (string) config('services.legacy_jwt_secret');
        if (strlen($secret) < 32) {
            throw new RuntimeException('JWT_SECRET_KEY must contain at least 32 characters.');
        }

        return $secret;
    }

    public function issueAccessToken(int $userId, string $email): string
    {
        $now = time();

        return JWT::encode([
            'sub' => (string) $userId,
            'email' => $email,
            'iat' => $now,
            'exp' => $now + ((int) config('services.access_token_expire_minutes', 30) * 60),
        ], $this->secret(), 'HS256');
    }

    public function issueResetToken(string $email): string
    {
        $now = time();

        return JWT::encode([
            'sub' => $email,
            'purpose' => 'password_reset',
            'iat' => $now,
            'exp' => $now + 900,
        ], $this->secret(), 'HS256');
    }

    public function decode(string $token): ?object
    {
        try {
            return JWT::decode($token, new Key($this->secret(), 'HS256'));
        } catch (Throwable) {
            return null;
        }
    }
}
