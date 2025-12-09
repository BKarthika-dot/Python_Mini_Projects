from flask import Blueprint,render_template,request,jsonify,redirect,url_for

views=Blueprint(__name__,"views")

@views.route("/")
def home():
    return render_template("index.html",name="Karthika",age=21)

# @views.route("/profile")
#def profile():
#   args=request.args             #for query parameters
#   name=args.get('name')
#   age=args.get('age')
#   return render_template("index.html",name=name,age=age)

@views.route("/profile")
def profile():
    return render_template("profile.html")


@views.route("/json")
def get_json():
    return jsonify({'name':'karthi','age':22})

@views.route("/data")   #getting json data
def get_data():
    data=request.json
    return jsonify(data)

@views.route("/go-to-home")   #redirecting to a diff page
def go_to_home():
    return redirect(url_for("views.home"))