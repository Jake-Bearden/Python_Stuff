
import requests
import time
from collections import defaultdict

BASE_URL = "https://api.scryfall.com/cards/search"

COLORS = {
    "W": "White",
    "U": "Blue",
    "B": "Black",
    "R": "Red",
    "G": "Green"
}


def get_color_name(identity):
    if not identity:
        return "Colorless"

    return " / ".join(
        COLORS[color] for color in "WUBRG"
        if color in identity
    )


def search_cards(keywords, max_price, colors):

    query_parts = [
        "f:commander",
        f"id<={colors}",
        f"usd<={max_price}"
    ]

    for keyword in keywords:
        query_parts.append(f'keyword:"{keyword}"')

    query = " ".join(query_parts)

    print(f"\nScryfall query: {query}")
    print("Searching...\n")

    matching_cards = {}

    next_url = BASE_URL
    params = {
        "q": query,
        "unique": "prints",
        "order": "usd",
        "dir": "asc"
    }

    try:
        while next_url:

            response = requests.get(
                next_url,
                params=params,
                headers={
                    "User-Agent": "MTGCardFinder/1.0",
                    "Accept": "application/json"
                },
                timeout=20
            )

            response.raise_for_status()
            data = response.json()

            for card in data["data"]:

                price = card.get("prices", {}).get("usd")

                if price is None:
                    continue

                price = float(price)

                if price > max_price:
                    continue

                card_id = card.get("oracle_id", card["id"])

                if (
                    card_id not in matching_cards
                    or price < matching_cards[card_id]["price"]
                ):

                    identity = card.get("color_identity", [])

                    identity = "".join(
                        color for color in "WUBRG"
                        if color in identity
                    )

                    matching_cards[card_id] = {
                        "name": card["name"],
                        "price": price,
                        "type": card.get("type_line", "Unknown"),
                        "mana_cost": card.get("mana_cost", ""),
                        "identity": identity,
                        "color_name": get_color_name(identity),
                        "set": card.get("set_name", "Unknown"),
                        "image": card.get("image_uris", {}).get(
                            "normal", "No image available"
                        ),
                        "url": card.get("scryfall_uri", "")
                    }

            next_url = data.get("next_page")
            params = None

            if next_url:
                time.sleep(0.1)

        return sorted(
            matching_cards.values(),
            key=lambda card: card["price"]
        )

    except requests.exceptions.RequestException as error:
        print(f"API Error: {error}")
        return []


def display_cards(cards):

    grouped_cards = defaultdict(list)

    for card in cards:
        grouped_cards[card["color_name"]].append(card)

    print("\n========== SEARCH RESULTS ==========")

    if not cards:
        print("No matching cards found.")
        return

    for color, group in sorted(grouped_cards.items()):

        print(f"\n{'=' * 40}")
        print(f"{color.upper()} ({len(group)} cards)")
        print("=" * 40)

        for card in group:

            print(f"\nCard: {card['name']}")
            print(f"Price: ${card['price']:.2f}")
            print(f"Type: {card['type']}")
            print(f"Mana Cost: {card['mana_cost']}")
            print(f"Color Identity: {card['identity'] or 'C'}")
            print(f"Set: {card['set']}")
            print(f"Scryfall: {card['url']}")

    print("\n====================================")
    print(f"Total matching cards: {len(cards)}")


def main():

    print("================================")
    print("       MTG COMMANDER FINDER")
    print("================================")

    keywords_input = input(
        "\nEnter keywords separated by commas: "
    )

    keywords = [
        word.strip()
        for word in keywords_input.split(",")
        if word.strip()
    ]

    if not keywords:
        print("Enter at least one keyword.")
        return

    colors = input(
        "\nEnter Commander colors (WUBRG): "
    ).strip().upper()

    if not colors:
        colors = "WUBRG"

    if colors == "C":
        colors = "C"

    elif (
        any(color not in "WUBRG" for color in colors)
        or len(set(colors)) != len(colors)
    ):
        print("Invalid color identity.")
        return

    try:
        max_price = float(
            input("\nMaximum card price ($): ")
        )

        if max_price < 0:
            print("Price cannot be negative.")
            return

    except ValueError:
        print("Enter a valid price.")
        return

    cards = search_cards(
        keywords,
        max_price,
        colors
    )

    display_cards(cards)


if __name__ == "__main__":
    main()
