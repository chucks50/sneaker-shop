<?php

namespace App\Http\Middleware;

use App\Models\User;
use App\Services\TokenService;
use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class AuthenticateJwt
{
    public function handle(Request $request, Closure $next): Response
    {
        $token = $request->bearerToken();
        $payload = $token ? app(TokenService::class)->decode($token) : null;
        $userId = $payload->sub ?? null;

        if (! $userId || ! ctype_digit((string) $userId)) {
            return response()->json(['detail' => $token ? 'Invalid token' : 'Authentication required'], 401);
        }

        $user = User::query()->find((int) $userId);
        if (! $user || ! $user->is_active) {
            return response()->json(['detail' => 'User not found'], 401);
        }

        $request->attributes->set('current_user', $user);

        return $next($request);
    }
}
