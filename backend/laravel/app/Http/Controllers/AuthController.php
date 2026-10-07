<?php

namespace App\Http\Controllers;

use App\Models\User;
use App\Services\TokenService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Mail;

class AuthController extends Controller
{
    private function publicUser(User $user): array
    {
        return [
            'id' => (int) $user->id,
            'email' => $user->email,
            'first_name' => $user->first_name,
            'last_name' => $user->last_name,
            'is_active' => (bool) $user->is_active,
        ];
    }

    public function register(Request $request): JsonResponse
    {
        $data = $request->validate([
            'first_name' => ['required', 'string', 'max:100'],
            'last_name' => ['required', 'string', 'max:100'],
            'email' => ['required', 'email', 'max:255'],
            'password' => ['required', 'string', 'min:8'],
        ]);
        if (User::query()->where('email', $data['email'])->exists()) {
            return response()->json(['detail' => 'Email already registered'], 400);
        }

        $user = User::query()->create([
            'first_name' => $data['first_name'],
            'last_name' => $data['last_name'],
            'email' => $data['email'],
            'password_hash' => Hash::make($data['password']),
            'is_active' => true,
        ]);

        return response()->json($this->publicUser($user));
    }

    public function login(Request $request, TokenService $tokens): JsonResponse
    {
        $data = $request->validate([
            'email' => ['required', 'email'],
            'password' => ['required', 'string'],
        ]);
        $user = User::query()->where('email', $data['email'])->first();
        if (! $user || ! Hash::check($data['password'], $user->password_hash)) {
            return response()->json(['detail' => 'Invalid email or password'], 401);
        }

        return response()->json([
            'access_token' => $tokens->issueAccessToken((int) $user->id, $user->email),
            'token_type' => 'bearer',
            'user' => $this->publicUser($user),
        ]);
    }

    public function me(Request $request): JsonResponse
    {
        return response()->json($this->publicUser($request->attributes->get('current_user')));
    }

    public function forgotPassword(Request $request, TokenService $tokens): JsonResponse
    {
        $data = $request->validate(['email' => ['required', 'email']]);
        $user = User::query()->where('email', $data['email'])->first();

        if ($user) {
            $token = $tokens->issueResetToken($user->email);
            Log::warning('Password reset token for '.$user->email.': '.$token);

            if (config('mail.default') !== 'log') {
                try {
                    Mail::raw(
                        "Your Sneaker Shop password reset token is:\n\n{$token}\n\nIt expires in 15 minutes.",
                        fn ($message) => $message->to($user->email)->subject('Password reset'),
                    );
                } catch (\Throwable $exception) {
                    report($exception);
                }
            }
        }
        return response()->json([
            'message' => 'If an account with that email exists, a password reset email has been sent.',
        ]);
    }

    public function resetPassword(Request $request, TokenService $tokens): JsonResponse
    {
        $data = $request->validate([
            'email' => ['required', 'email'],
            'reset_token' => ['required', 'string'],
            'new_password' => ['required', 'string', 'min:8'],
        ]);
        $user = User::query()->where('email', $data['email'])->first();
        if (! $user) {
            return response()->json(['detail' => 'User not found'], 404);
        }
        $payload = $tokens->decode($data['reset_token']);
        if (! $payload || ($payload->purpose ?? null) !== 'password_reset') {
            return response()->json(['detail' => 'Invalid or expired reset token'], 400);
        }
        if (strcasecmp((string) ($payload->sub ?? ''), $data['email']) !== 0) {
            return response()->json(['detail' => 'Reset token does not match this account'], 400);
        }

        $user->password_hash = Hash::make($data['new_password']);
        $user->save();

        return response()->json(['message' => 'Password updated successfully.']);
    }
}
