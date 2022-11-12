import sys


def test_signature_message(monkeypatch):
    sys.path.append("src")

    from pycardano import Address

    # Testnet address
    monkeypatch.setattr(
        "os.environ",
        {
            "NETWORK_MODE": "testnet",
        },
    )

    from lib import cardano_tools

    sig = "84584da301276761646472657373581d60a64aa1009d0f106fd742a79ee68bd9a5fd815ffa587d6d0aa68cb51e045820f84f04c0054dbbb0a7fcbd1584dac460cbd1b14723a6e9d2571477ba21644858a166686173686564f451507963617264616e6f20697320636f6f6c5840a3f2def0bc5cddbc5171226b45cf3cb37c55239e00f0abebc8aabc5242ea17f21130c928477ef66dca86327a8599b935ce3c9156ed15a5f1c328d04079bfff04"
    message = "Pycardano is cool"
    address = "stake_test1uzny4ggqn583qm7hg2neae5tmxjlmq2llfv86mg256xt28sv20c2r"

    assert cardano_tools.signature_message(sig, address) == message

    # Signed by pycardano - only payment part
    sig = {
        "signature": "84582aa201276761646472657373581d60a64aa1009d0f106fd742a79ee68bd9a5fd815ffa587d6d0aa68cb51ea166686173686564f451507963617264616e6f20697320636f6f6c58403a59f8aac42b5f64bf604bbd33b705a9d5bf2712574058df11c0da7a3855ba3a7cb2da80deff27f521214df8efb7a7957e0a2738830d030eec5cc4ce82229a04",
        "key": "a4010103272006215820f84f04c0054dbbb0a7fcbd1584dac460cbd1b14723a6e9d2571477ba21644858",
    }
    message = "Pycardano is cool"
    address = "stake_test1uzny4ggqn583qm7hg2neae5tmxjlmq2llfv86mg256xt28sv20c2r"

    assert cardano_tools.signature_message(sig, address) == message

    # Wrong address
    sig = "84584da301276761646472657373581d60a64aa1009d0f106fd742a79ee68bd9a5fd815ffa587d6d0aa68cb51e045820f84f04c0054dbbb0a7fcbd1584dac460cbd1b14723a6e9d2571477ba21644858a166686173686564f451507963617264616e6f20697320636f6f6c5840a3f2def0bc5cddbc5171226b45cf3cb37c55239e00f0abebc8aabc5242ea17f21130c928477ef66dca86327a8599b935ce3c9156ed15a5f1c328d04079bfff04"
    message = "Pycardano is cool"
    address = "stake_test1upmpu3pjqgjx4amy8ulv4fxpy26cmh553yhxhjhqurz9y7qrymfne"

    assert cardano_tools.signature_message(sig, address) is None
