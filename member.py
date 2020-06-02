from datetime import datetime, timedelta

class Member():
    def __init__(self, name, first_msg:datetime, last_msg:datetime, db_update:datetime):
        self.name = name
        self.first_msg = first_msg
        self.last_msg = last_msg
        self.anciennete = last_msg - first_msg
        if last_msg < db_update - timedelta(days=15):
            self.status = "past"        
        else:
            self.status = "present"

    def show(self):
        f_msg = self.first_msg.strftime("%b %Y")
        l_msg = self.last_msg.strftime("%b %Y")
        if self.status == "past":
            return f"{f_msg} - {l_msg}"
        if self.status == "present":
            return f"Since {f_msg}"
