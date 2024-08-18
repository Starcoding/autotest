from time import sleep

from flasgger import Swagger
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

sleep(3)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://test_user:test_pass@db:5432/humans_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

swagger = Swagger(app)



# Определяем модель Human
class Human(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.String(10), nullable=False)


# Создаем таблицы
with app.app_context():
    db.create_all()

# Эндпоинты для CRUD операций

@app.route("/", methods=["GET"])
def hello():
    return "Привет!"

# Получить всех людей
@app.route("/humans", methods=["GET"])
def get_humans():
    """
    Retrieve all humans
    ---
    responses:
      200:
        description: A list of humans
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                description: The human ID
              name:
                type: string
                description: The human's name
              age:
                type: integer
                description: The human's age
              sex:
                type: string
                description: The human's sex
    """
    humans = Human.query.all()
    return jsonify(
        [{"id": h.id, "name": h.name, "age": h.age, "sex": h.sex} for h in humans]
    )


@app.route("/humans/<int:id>", methods=["GET"])
def get_human(id):
    """
    Retrieve a human by ID
    ---
    parameters:
      - in: path
        name: id
        type: integer
        required: true
        description: The human ID
    responses:
      200:
        description: A human object
        schema:
          type: object
          properties:
            id:
              type: integer
              description: The human ID
            name:
              type: string
              description: The human's name
            age:
              type: integer
              description: The human's age
            sex:
              type: string
              description: The human's sex
      404:
        description: Human not found
    """
    human = Human.query.get_or_404(id)
    return jsonify(
        {"id": human.id, "name": human.name, "age": human.age, "sex": human.sex}
    )


@app.route("/humans", methods=["POST"])
def create_human():
    """
    Create a new human
    ---
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              description: The human's name
            age:
              type: integer
              description: The human's age
            sex:
              type: string
              description: The human's sex
    responses:
      201:
        description: The human was created successfully
        schema:
          type: object
          properties:
            id:
              type: integer
              description: The created human's ID
    """
    data = request.json
    new_human = Human(name=data["name"], age=data["age"], sex=data["sex"])
    db.session.add(new_human)
    db.session.commit()
    return jsonify({"id": new_human.id}), 201


@app.route("/humans/<int:id>", methods=["PUT"])
def update_human(id):
    """
    Update an existing human
    ---
    parameters:
      - in: path
        name: id
        type: integer
        required: true
        description: The human ID
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              description: The human's name
            age:
              type: integer
              description: The human's age
            sex:
              type: string
              description: The human's sex
    responses:
      200:
        description: The updated human object
        schema:
          type: object
          properties:
            id:
              type: integer
              description: The human ID
            name:
              type: string
              description: The human's name
            age:
              type: integer
              description: The human's age
            sex:
              type: string
              description: The human's sex
      404:
        description: Human not found
    """
    human = Human.query.get_or_404(id)
    data = request.json
    human.name = data.get("name", human.name)
    human.age = data.get("age", human.age)
    human.sex = data.get("sex", human.sex)
    db.session.commit()
    return jsonify(
        {"id": human.id, "name": human.name, "age": human.age, "sex": human.sex}
    )


@app.route("/humans/<int:id>", methods=["DELETE"])
def delete_human(id):
    """
    Delete a human by ID
    ---
    parameters:
      - in: path
        name: id
        type: integer
        required: true
        description: The human ID
    responses:
      204:
        description: The human was deleted successfully
      404:
        description: Human not found
    """
    human = Human.query.get_or_404(id)
    db.session.delete(human)
    db.session.commit()
    return jsonify({"message": f"id {id} deleted"}), 204


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)
