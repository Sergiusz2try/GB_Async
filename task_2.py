import json
import os


def write_order_to_json(item, quantity, price, buyer, date):
    data_order = {
        "Item": item,
        "Quanitity": quantity,
        "Price": price,
        "Buyer": buyer,
        "Data": date,
    }

    with open("data/orders.json") as f:
        data = json.load(f)

    data["orders"].append(data_order)

    with open("data/orders.json", "w") as f:
        json.dump(data, f, indent=4)


if __name__ == "__main__":
    write_order_to_json("Iphone 1", "1", "500$", "Json Dude", "14.12.22")