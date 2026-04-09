from flask import Flask, render_template, request, redirect, url_for
import yaml
import os

from automation.deploy_config import deploy_config

app = Flask(__name__)

ROUTERS_FILE = "routers.yml"


def load_routers():
    if not os.path.exists(ROUTERS_FILE):
        return {"routers": []}

    with open(ROUTERS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data:
        return {"routers": []}

    if "routers" not in data:
        data["routers"] = []

    return data


def save_routers(data):
    with open(ROUTERS_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


@app.route("/")
def index():
    data = load_routers()
    return render_template("index.html", routers=data["routers"])


@app.route("/add_router", methods=["POST"])
def add_router():
    data = load_routers()

    new_router = {
        "name": request.form["name"].strip(),
        "ip": request.form["ip"].strip(),
        "device_type": request.form["device_type"].strip(),
        "username": request.form["username"].strip(),
        "password": request.form["password"].strip(),
        "loopback_ip": request.form["loopback_ip"].strip()
    }

    data["routers"].append(new_router)
    save_routers(data)

    return redirect(url_for("index"))

@app.route("/deploy")
def deploy():
    results = deploy_config()
    return render_template("result.html", results=results)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=False)