def note_password_complexity():
    return 'min 6 chars, max 25 chars'

def validate_password_complexity(password):
    if len(password) < 6:
        return 'Enter a value at least 6 characters long'
    if len(password) > 25:
        return 'Enter a value less than 25 characters long'
    return True
