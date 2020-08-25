from . import bp, errors

from flask import request, jsonify, make_response

import logging
from typing import Dict, Union

from app import db

from app.models import Depot


def is_float(x: any):
    return isinstance(x, float)


def check_depot(depot):
    params = ["latitude", "longitude"]

    # Checking if all input parameters are present
    for param in params:
        if param not in depot:
            raise errors.InvalidUsage("Incorrect depot!", invalid_object=depot)

    if not is_float(depot["latitude"]):
        raise errors.InvalidUsage("Invalid latitude", invalid_object=depot)

    if depot["latitude"] < -90 or 90 < depot["latitude"]:
        raise errors.InvalidUsage("Invalid latitude", invalid_object=depot)

    if not is_float(depot["longitude"]):
        raise errors.InvalidUsage("Invalid longitude", invalid_object=depot)

    if depot["longitude"] < -180 or 180 < depot["longitude"]:
        raise errors.InvalidUsage("Invalid longitude", invalid_object=depot)


@bp.route("/depot", methods=["GET", "POST"])
def depots():

    if request.method == "GET":
        depot = Depot.query.get_or_404(1).to_dict()
        return jsonify({"depot": depot})

    if request.method == "POST":

        if not request.is_json:
            raise errors.InvalidUsage(
                "Incorrect request format! Request data must be JSON"
            )

        data = request.get_json(silent=True)
        if not data:
            raise errors.InvalidUsage(
                "Invalid JSON received! Request data must be JSON"
            )

        if "depots" in data:
            depots = data["depots"]
        else:
            raise errors.InvalidUsage("'depots' missing in request data")

        if not isinstance(depots, list):
            raise errors.InvalidUsage("'depots' should be list")

        if not depots:
            raise errors.InvalidUsage("'depots' is empty")
        elif len(depots) != 1:
            raise errors.InvalidUsage("'depots' contains more than one object")

        depot = depots[0]

        # Checking if depot is valid
        check_depot(depot)

        # Deleting every depot
        Depot.query.delete()

        # Filtering the dict
        params = ["latitude", "longitude", "user_id"]
        depot = {param: depot[param] for param in params}

        # Using dict unpacking for creation
        new_depot = Depot(**depot)
        db.session.add(new_depot)

        db.session.commit()

        depot["id"] = new_depot.id

        return make_response(jsonify({"depots": [depot]}), 201)


@bp.route("/depot/<int:id>", methods=["GET", "PUT"])
def depot(id: int):
    if request.method == "GET":
        return Depot.query.get_or_404(id).to_dict()
    if request.method == "PUT":

        depot: Depot = Depot.query.get_or_404(id)

        if not request.is_json:
            raise errors.InvalidUsage(
                "Incorrect request format! Request data must be JSON"
            )

        data: Union[dict, None] = request.get_json(silent=True)
        if not data:
            raise errors.InvalidUsage(
                "Invalid JSON received! Request data must be JSON"
            )

        params = ["latitude", "longitude", "user_id"]

        new_depot: Dict[str, any] = {}

        for param in params:
            if param in data:
                new_depot[param] = data[param]
            else:
                raise errors.InvalidUsage(f"{param} missing in request data")

        # Validate new data
        check_depot(new_depot)

        # Update values in DB
        depot.latitude = new_depot["latitude"]
        depot.longitude = new_depot["longitude"]
        depot.user_id = new_depot["user_id"]

        db.session.commit()

        return make_response(jsonify(depot.to_dict()), 200)
