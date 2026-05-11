def enroll_member(member_request):
    member = create_member(member_request)
    member.status = "ACTIVE"

    # BUG: card assignment is not invoked here.
    # claim submission expects member.card_id to be populated.
    return member
