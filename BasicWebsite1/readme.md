
---

This is a simple Flask-based Python web project that demonstrates the essentials of building a small web application.
It includes:

* 🔗 **Flask routing**
* 🧩 **Blueprints**
* 🖼️ **Template rendering**
* 📤 **Passing data to templates**
* 🧾 **JSON responses**
* ❓ **Query parameters**
* 📥 **Handling JSON input**
* 🔄 **Redirecting between routes**
* 🏗️ **Basic template inheritance**
* ⚡ **Using JavaScript in templates**

---

## 🚀 How It Works

### **app.py**

* 🏗️ Creates the Flask app
* 📦 Registers a Blueprint
* ▶️ Runs the server on port **8000**

---

### **views.py**

Contains routes for:

* `/views/` → 🏡 Renders the homepage
* `/views/profile` → 👤 Renders a profile template
* `/views/json` → 📄 Returns a JSON object using `jsonify()`
* `/views/data` → 📥 Accepts and returns JSON data
* `/views/go-to-home` → 🔁 Redirects to the home page using `redirect()` and `url_for()`

---

## 🎨 Templates

### **index.html**

* Uses Jinja2 template variables: `{{ name }}` and `{{ age }}`
* 🧱 Defines a block for template inheritance
* ⚡ Loads a JavaScript file (`index.js`)

### **profile.html**

* 🧩 Extends the main template using Jinja blocks (if implemented)

---


