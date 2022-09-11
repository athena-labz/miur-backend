import sys

from dataclasses import dataclass
from dotenv import load_dotenv


def test_signature_message(monkeypatch):
    sys.path.append("src")

    from pycardano import Address

    # Testnet address
    monkeypatch.setattr("os.environ", {
        "NETWORK_MODE": "testnet",
    })

    from lib import cardano_tools

    sig = "845869a3012704582060545b786d3a6f903158e35aae9b86548a99bc47d4b0a6f503ab5e78c1a9bbfc6761646472657373583900ddba3ad76313825f4f646f5aa6d323706653bda40ec1ae55582986a463e661768b92deba45b5ada4ab9e7ffd17ed3051b2e03500e0542e9aa166686173686564f452507963617264616e6f20697320636f6f6c2e58403b09cbae8d272ff94befd28cc04b152aea3c1633caffb4924a8a8c45be3ba6332a76d9f2aba833df53803286d32a5ee700990b79a0e86fab3cccdbfd37ce250f"
    message = "Pycardano is cool."
    address = "addr_test1qrwm5wkhvvfcyh60v3h44fknydcxv5aa5s8vrtj4tq5cdfrrueshdzujm6aytddd5j4eullazlknq5djuq6spcz596dqjvm8nu"

    assert cardano_tools.signature_message(sig, address) == message

    # Signed by pycardano - only payment part
    sig = "84584da301276761646472657373581d60ae31a2873ec4e89d478eee0137f1a41dc65c1b403224a8cafa85bb5f045820bff6dc39c2dd5684cd3015a65e9ea26ee1b3aa950b7de442c2dec9c289733e76a166686173686564f452507963617264616e6f20697320636f6f6c2e58409e88be86b5d60d2b14527443fcd334168109ee32bed9b2a646bf8f642b4067104f9062e9035ca88c9287cb9abbe3bfaf818fdfa2ee72b4ef5898530d6edb070c"
    message = "Pycardano is cool."
    address = "addr_test1qzhrrg588mzw38283mhqzdl35swuvhqmgqezf2x2l2zmkhaxf2ssp8g0zphaws48nmnghkd9lkq4l7jc04ks4f5vk50qdf28fq"

    assert cardano_tools.signature_message(sig, address) == message

    # Wrong address
    sig = "84584da301276761646472657373581d60ae31a2873ec4e89d478eee0137f1a41dc65c1b403224a8cafa85bb5f045820bff6dc39c2dd5684cd3015a65e9ea26ee1b3aa950b7de442c2dec9c289733e76a166686173686564f45826556e646572206e6f2063697263756e7374616e636573206c6f6f6b20626568696e6420796f7558406505e4066958920109a3057ac1d952434e570d794e7978776c63dbb741a2066da70f6bcb007dc882dc8a22d73f496f72994c5376be317bffc54806d5f9dbfa01"
    address = "addr_test1qrwm5wkhvvfcyh60v3h44fknydcxv5aa5s8vrtj4tq5cdfrrueshdzujm6aytddd5j4eullazlknq5djuq6spcz596dqjvm8nu"

    assert cardano_tools.signature_message(sig, address) is None