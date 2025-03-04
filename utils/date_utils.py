import datetime

def convert_date_to_age(birth_date):
    today = datetime.date.today()
    born = datetime.datetime.strptime(birth_date, "%Y-%m-%d").date()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))