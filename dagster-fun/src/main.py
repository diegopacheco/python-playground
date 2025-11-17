import dagster as dg

@dg.asset
def raw_data():
    return [1, 2, 3, 4, 5]

@dg.asset
def doubled_data(raw_data):
    return [x * 2 for x in raw_data]

@dg.asset
def summed_data(doubled_data):
    return sum(doubled_data)

all_assets_job = dg.define_asset_job("all_assets_job", selection="*")

defs = dg.Definitions(
    assets=[raw_data, doubled_data, summed_data],
    jobs=[all_assets_job]
)
