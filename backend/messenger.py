from parser import ParsedGift

class MessageGenerator:
    """
    Generates personalized, culturally appropriate thank-you messages.
    Strictly enforces:
    1. NEVER mention cash amounts under any circumstances.
    2. Specifically mention physical gifts.
    3. Respectfully address families jointly when applicable.
    4. Flag uncertain/unknown entries for manual review.
    """

    @classmethod
    def generate_message(cls, gift: ParsedGift) -> str:
        # 1. Salutation
        if gift.needs_review and gift.guest_name == "Unknown Guest":
            salutation = "Dear Respected Guest & Family,"
        elif gift.is_family:
            salutation = f"Dear {gift.guest_name} and family,"
        else:
            salutation = f"Dear {gift.guest_name},"

        # 2. Body based on gift type
        if gift.is_cash:
            # STRICT CASH RULE: No amount mentioned! Only gratitude for blessings and generosity.
            body = (
                f"{salutation}\n\n"
                f"Thank you so much for joining us in celebrating our wedding. "
                f"Your warm presence and generous blessing meant the world to us and our family. "
                f"We are deeply grateful for your thoughtfulness and love on our special day.\n\n"
                f"Warmest regards,\nFarhana & Family"
            )
        elif gift.gift_description and gift.gift_description.lower() not in ["gift", "big box"]:
            # Specific item mentioned
            body = (
                f"{salutation}\n\n"
                f"Thank you so much for being part of our wedding celebrations. "
                f"We truly appreciate the lovely {gift.gift_description} you gave us - it was so thoughtful "
                f"of you, and we will cherish it for years to come. Thank you for your heartfelt blessings!\n\n"
                f"Warmest regards,\nFarhana & Family"
            )
        else:
            # Box or unspecified gift
            body = (
                f"{salutation}\n\n"
                f"Thank you so much for celebrating our wedding with us. "
                f"We are so grateful for your kind gift and heartfelt blessings on our new journey together.\n\n"
                f"Warmest regards,\nFarhana & Family"
            )

        # 3. Add reviewer flag if manual review is needed
        if gift.needs_review:
            body += f"\n\n[ATTENTION: Please verify guest details before sending: '{gift.raw_text}']"

        return body

    @classmethod
    def batch_generate(cls, gifts: list[ParsedGift]) -> list[dict]:
        results = []
        for g in gifts:
            item = g.to_dict()
            item["thank_you_message"] = cls.generate_message(g)
            results.append(item)
        return results
