import secrets  # Use secrets for better randomness than 'random'


def generate_referral_code(length=5):
    # Alphabet without confusing characters
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    code = "".join(secrets.choice(chars) for _ in range(length))
    return f"LOAN-{code}"
