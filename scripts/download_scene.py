from pystac_client import Client
import planetary_computer 
import rasterio
from rasterio.windows import Window
import numpy as np
from PIL import Image
import torch
import open_clip

#downloading a satellite tile
catalog = Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1",
    modifier=planetary_computer.sign_inplace,
)

bbox = [77.05, 28.45, 77.35, 28.75]

search = catalog.search(
    collections = ["sentinel-2-l2a"],
    bbox=bbox,
    datetime="2026-01-01/2026-03-01",
)

items = list(search.items())
item = items[0]

print("using scene: ", item.id)
print("available assets: ", list(item.assets.keys()))

visual_asset = item.assets["visual"]

gdal_env = rasterio.Env(
    GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
    CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
    GDAL_HTTP_MAX_RETRY=5,
    GDAL_HTTP_RETRY_DELAY=1,
)

with gdal_env:
    with rasterio.open(visual_asset.href) as src:
        print("full scene size: ", src.width, src.height)
        print("number of bands: ", src.count)
        print("coordinate reference system: ", src.crs)

        window = Window(col_off=0, row_off=0, width=512, height=512)
        chunk = src.read(window=window)
print("downloaded chunk shape: ", chunk.shape)

#GeoRSCLIP readable conversion

chunk_rearranged = chunk.transpose(1,2,0) #changes dimensions to H, W, B, like how PIL expects it
tile_image = Image.fromarray(chunk_rearranged).convert("RGB") #array of numbers changed to PIL image object and RBG ensures 3 color channels

#load GeoRSCLIP

model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32-quickgelu", pretrained="openai")
checkpoint = torch.load(r"models\ckpt\RS5M_ViT-B-32_RET-2.pt", map_location="cpu")
model.load_state_dict(checkpoint, strict="False")
model.eval()

tile_input = preprocess(tile_image).unsqueeze(0)

with torch.no_grad():
    tile_features = model.encode_image(tile_input)

print("tile vector shape: ", tile_features.shape)
print("first 5 numbers: ", tile_features[0][:5])

# --- Part 5: grab a second scene at a different date, same area ---

# Filter to a single MGRS tile so we're comparing the exact same location
tile_id = items[0].id.split("_")[-2]
same_tile_items = [i for i in items if i.id.split("_")[-2] == tile_id]

items_sorted = sorted(same_tile_items, key=lambda i: i.datetime)
item_early = items_sorted[0]
item_late = items_sorted[-1]

print("comparing tile:", tile_id, "| scenes available for this tile:", len(items_sorted))

print("earliest scene: ", item_early.id)
print("latest scene: ", item_late.id)

def fetch_and_embed(item):
    asset = item.assets["visual"]
    with gdal_env:
        with rasterio.open(asset.href) as src:
            chunk = src.read(window=window)
    rearranged = chunk.transpose(1, 2, 0)
    tile_image = Image.fromarray(rearranged).convert("RGB")
    tile_input = preprocess(tile_image).unsqueeze(0)
    with torch.no_grad():
        features = model.encode_image(tile_input)
    return features

features_early = fetch_and_embed(item_early)
features_late = fetch_and_embed(item_late)

# --- Part 6: compare the two vectors ---

vec1 = features_early[0] / features_early[0].norm()
vec2 = features_late[0] / features_late[0].norm()

similarity = torch.dot(vec1, vec2)
print("cosine similarity between earliest and latest: ", similarity.item())
