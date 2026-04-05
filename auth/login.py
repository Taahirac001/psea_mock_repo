def login(user):
    # Step 1: Check account status
    if user.get("status") == "EXPIRED":
        raise Exception("Login failed: account expired")

    # Step 2: Generate token
    token = generate_token(user)

    # Step 3: Create session
    session = create_session(token)

    return session


def generate_token(user):
    # Simulated failure case
    if user.get("userId") == "123":
        raise Exception("Token generation failed")

    return "token_abc"


def create_session(token):
    # Simulated downstream dependency
    if token == "token_abc":
        return {"session": "valid"}

    raise Exception("Session creation failed")