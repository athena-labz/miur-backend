from fixtures import api


def test_register(api):
    client, app = api

    from model import db, ProdUser
    

    with app.app_context():
        email = "alice@email.com"
        password = "password"

        # Create a user
        user = ProdUser.register(email, password)

        assert ProdUser.query.count() == 1

        assert user.email == email
        assert user.password_hash != password
        assert user.salt != password

        assert user.stake_address is None
        assert user.payment_address is None

        assert user.is_email_verified == False
        assert user.is_address_verified == False

        # Try to sign in with the wrong password
        assert ProdUser.login(email, "wrong_password") is None

        # Sign in with the correct password
        assert ProdUser.login(email, password).id == user.id