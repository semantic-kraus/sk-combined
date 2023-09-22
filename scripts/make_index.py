from datetime import datetime

now = datetime.now()


with open("./scripts/templates/template_index.html", "r") as f:
    data = f.read()

data = data.replace("###DATUM###", f"{now}")

with open("./html/index.html", "w") as f:
    f.write(data)
