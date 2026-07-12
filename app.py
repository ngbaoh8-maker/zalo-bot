from flask import Flask, render_template, request, jsonify
import time

app = Flask(__name__)

# ===== HÀM CHECK GIẢ LẬP (AN TOÀN) =====
def check_fc_account(email, password):
    """
    ⚠️ DEMO ONLY
    Không login thật, không gửi request tới EA
    """

    time.sleep(1)  # giả lập delay

    # logic giả
    if len(email) < 5 or len(password) < 6:
        return {
            "status": "die",
            "message": "Sai định dạng"
        }

    if "@" in email:
        return {
            "status": "live",
            "message": "Acc hợp lệ (demo)",
            "level": "45",
            "team_ovr": "118"
        }

    return {
        "status": "die",
        "message": "Không tồn tại"
    }


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        result = check_fc_account(email, password)
    return render_template("index.html", result=result)


@app.route("/api/check", methods=["POST"])
def api_check():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    return jsonify(check_fc_account(email, password))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
