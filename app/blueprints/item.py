from flask import Blueprint, jsonify

item_bp = Blueprint("item", __name__, url_prefix="/items")

@item_bp.get("/")
def list_items():
    return jsonify(items=[])



# test by arima2
# test by fujita
#t
#test by yamamoto
# test by mukoyama

あだだだだだだ