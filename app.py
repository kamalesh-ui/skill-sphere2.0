from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import requests
import subprocess
import tempfile
import os
import sys

app = Flask(__name__)

# ---------- DATABASE ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "chat.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

API_KEY = "ddc-a4f-15a26a02194b4d33a2a07738f261aebb"   # ← keep your key here


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20))
    content = db.Column(db.Text)
    mode = db.Column(db.String(50))


with app.app_context():
    db.create_all()


# ---------- SYSTEM PROMPTS ----------
def get_system_prompt(mode):
    prompts = {
        "python": "You are a Python tutor. Teach clearly with examples.",
        "web": "Teach HTML, CSS and JavaScript step by step.",
        "java": "You are a Java tutor.",
        "error": "Explain coding errors clearly.",
        "c": "Teach C programming simply.",
        "c++": "Teach modern C++ programming.",
        "mongodb": "Teach MongoDB queries with examples."
    }
    return prompts.get(mode, "You are a helpful programming tutor.")


# ---------- MODEL ----------
def get_model(mode):
    # Use ONE stable model supported by your API
    return "provider-1/gpt-oss-20b"


# ---------- ROUTES ----------
@app.route("/")
def home():
    messages = Message.query.all()
    return render_template("index.html", messages=messages)


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_input = data.get("message", "")
    mode = data.get("mode", "python")

    # Save user message
    db.session.add(Message(role="user", content=user_input, mode=mode))
    db.session.commit()

    # Load conversation history
    history = Message.query.filter_by(mode=mode).all()
    chat_messages = [{"role": m.role, "content": m.content} for m in history]

    payload = {
        "model": get_model(mode),
        "messages": [
            {"role": "system", "content": get_system_prompt(mode)},
            *chat_messages
        ]
    }

    try:
        response = requests.post(
            "https://api.a4f.co/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=60
        )

        result = response.json()
        print("API RESPONSE:", result)  # DEBUG

        if "choices" in result:
            ai_reply = result["choices"][0]["message"]["content"]
        else:
            ai_reply = f"⚠️ API Error: {result}"

    except Exception as e:
        ai_reply = f"⚠️ Server error: {str(e)}"

    # Save AI reply
    db.session.add(Message(role="assistant", content=ai_reply, mode=mode))
    db.session.commit()

    return jsonify({"reply": ai_reply})


# ---------- CODE RUNNER ----------
@app.route("/run_code", methods=["POST"])
def run_code():
    data = request.json
    code = data.get("code", "")
    mode = data.get("mode", "python")

    try:
        ext_map = {
            "python": ".py",
            "java": ".java",
            "c": ".c",
            "c++": ".cpp"
        }

        ext = ext_map.get(mode, ".txt")

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
            f.write(code.encode())
            filename = f.name

        # ---------- EXECUTION ----------
        if mode == "python":
            cmd = [sys.executable, filename]

        elif mode == "java":
            subprocess.run(["javac", filename], check=True)
            classname = os.path.basename(filename).replace(".java", "")
            cmd = ["java", "-cp", os.path.dirname(filename), classname]

        elif mode == "c":
            exe = filename.replace(".c", ".exe")
            subprocess.run(["gcc", filename, "-o", exe], check=True)
            cmd = [exe]

        elif mode == "c++":
            exe = filename.replace(".cpp", ".exe")
            subprocess.run(["g++", filename, "-o", exe], check=True)
            cmd = [exe]

        else:
            return jsonify({"error": "Execution not supported"})

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            shell=(os.name == "nt")
        )

        return jsonify({
            "output": result.stdout,
            "error": result.stderr
        })

    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Compilation error"})
    except Exception as e:
        return jsonify({"error": str(e)})


# ---------- EXTRA PAGES ----------
@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/history")
def history():
    messages = Message.query.all()
    return render_template("history.html", messages=messages)


@app.route("/clear_history")
def clear_history():
    db.session.query(Message).delete()
    db.session.commit()
    return redirect(url_for("history"))


@app.route("/settings")
def settings():
    return render_template("settings.html")


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)