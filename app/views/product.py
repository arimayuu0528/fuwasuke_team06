from flask import Blueprint, jsonify

product_bp = Blueprint("product", __name__, url_prefix="/products")

@product_bp.get("/")
def list_products():
    return jsonify(products=[])
