import os
import re
import random
from flask import Flask, request, jsonify

app = Flask(__name__)

# Predefined color and font lists
COLORS = [
    "#ff00ff",  # Neon Pink
    "#00ff00",  # Neon Green
    "#ffcc00",  # Bright Yellow
    "#00ffff",  # Cyan
    "#ff4500",  # Neon Orange
    "#ff1493",  # Deep Pink
    "#39ff14",  # Electric Green
    "#ff5e00"   # Bright Orange
]

FONTS = [
    "'Comic Sans MS'",
    "cursive",
    "'Courier New', monospace",
    "'Verdana', sans-serif",
    "'Arial Black', sans-serif",
    "'Georgia', serif",
    "'Times New Roman', serif"
]

def convert_markdown_bold(text: str) -> str:
    """
    Converts markdown bold (**bold**) to HTML <b>bold</b>.
    """
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

def random_style() -> str:
    """
    Generates a random inline style string with color, font, and text-shadow.
    """
    color = random.choice(COLORS)
    font = random.choice(FONTS)
    shadow_color = random.choice(COLORS)
    return f"color: {color}; font-family: {font}; text-shadow: 2px 2px 4px {shadow_color};"

def adjust_cloze_numbers(text: str, decrement: int) -> str:
    """
    Adjusts the numbering of cloze deletions in the given text by decrementing each number by 'decrement',
    ensuring that the new number is at least 1.
    """
    def repl(match):
        num = int(match.group(1))
        new_num = num - decrement
        if new_num < 1:
            new_num = 1
        # Reconstruct the cloze deletion with the adjusted number, preserving the inner content
        return f"{{{{c{new_num}::{match.group(2)}}}}}"
    return re.sub(r"\{\{c(\d+)::(.*?)\}\}", repl, text)

def remove_and_adjust_cloze_from_first_sentence(card: str) -> str:
    """
    Removes cloze deletion wrappers from the first sentence of a card (text before the first <br><br>)
    and adjusts the numbering of cloze deletions in the remainder of the card by decrementing them
    by the number of cloze deletions removed.
    """
    parts = card.split("<br><br>", 1)
    if parts:
        first_sentence = parts[0]
        # Count cloze deletions in the first sentence
        cloze_matches = re.findall(r"\{\{c\d+::(.*?)\}\}", first_sentence)
        count_removed = len(cloze_matches)
        # Remove cloze wrappers from the first sentence (retain the inner text)
        first_sentence_clean = re.sub(r"\{\{c\d+::(.*?)\}\}", r"\1", first_sentence)
        if len(parts) > 1:
            rest = parts[1]
            # Adjust cloze numbering in the rest of the card
            rest_adjusted = adjust_cloze_numbers(rest, count_removed)
            return first_sentence_clean + "<br><br>" + rest_adjusted
        else:
            return first_sentence_clean
    return card

def process_card(card: str) -> str:
    """
    Processes a single card string by:
      1) Removing internal newlines/spaces,
      2) Converting **bold** to <b>bold</b>,
      3) Removing cloze deletion wrappers from the first sentence and adjusting subsequent numbering,
      4) Wrapping the result in a <span> with a random inline style.
    """
    card = card.replace("\n", " ").strip()
    card = convert_markdown_bold(card)
    card = remove_and_adjust_cloze_from_first_sentence(card)
    style = random_style()
    return f'<span style="{style}">{card}</span>'

def enforce_single_line_cards(output: str) -> str:
    """
    Splits the raw output by double newlines (each card separated by a blank line),
    processes each card, and rejoins them so each card is on a separate line of HTML.
    """
    raw_cards = output.split("\n\n")
    processed_cards = [process_card(card) for card in raw_cards if card.strip()]
    return "\n".join(processed_cards)

@app.route("/process", methods=["POST"])
def process():
    data = request.get_json()
    raw_text = data.get("raw_text", "")
    processed_text = enforce_single_line_cards(raw_text)
    # Wrap the processed text in triple backticks to display as a code block
    wrapped_output = "```\n" + processed_text + "\n```"
    return jsonify({"processed_text": wrapped_output})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
