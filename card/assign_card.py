def assign_card(member):
    card = create_card_for_member(member.id)
    if not card:
        return None
    member.card_id = card.id
    return card
