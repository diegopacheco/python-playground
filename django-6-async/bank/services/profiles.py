from ..domain.errors import DuplicateEmail, NotFound
from ..domain.identity import new_account_number, parse_email, parse_name
from ..models import Account, Profile


async def create_profile(full_name, email):
    name = parse_name(full_name)
    address = parse_email(email)
    if await Profile.objects.filter(email=address).aexists():
        raise DuplicateEmail(f"email '{address}' is already registered")
    profile = await Profile.objects.acreate(full_name=name, email=address)
    await Account.objects.acreate(profile=profile, number=new_account_number())
    return await get_profile(profile.pk)


async def get_profile(profile_id):
    profile = await Profile.objects.select_related("account").filter(pk=profile_id).afirst()
    if profile is None:
        raise NotFound(f"profile {profile_id} not found")
    return profile


async def list_profiles():
    query = Profile.objects.select_related("account")
    return [profile async for profile in query]
