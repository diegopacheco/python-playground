from ...services import profiles
from ..http import endpoint, json_response, read_body, require
from ..presenters import profile_json


@endpoint("GET", "POST")
async def collection(request):
    if request.method == "GET":
        found = await profiles.list_profiles()
        return json_response({"profiles": [profile_json(p) for p in found]})
    full_name, email = require(read_body(request), "full_name", "email")
    profile = await profiles.create_profile(full_name, email)
    return json_response(profile_json(profile), status=201)


@endpoint("GET")
async def detail(request, profile_id):
    profile = await profiles.get_profile(profile_id)
    return json_response(profile_json(profile))
