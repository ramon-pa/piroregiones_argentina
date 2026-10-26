"""Batch tasks shared by the export steps (02, 04): launch a grouped area sum to Drive, list our
tasks, and download the CSVs. No ``ee.*`` at module level, as in constants.py.

The shape of the export (one integer code, one grouped sum of pixel area, a rectangle as the
geometry) is the fire team's, statistics/burnable_export.py.
"""
import json
import os
from pathlib import Path

from utils import constants as C

LIVE = {"READY", "RUNNING", "COMPLETED"}  # states that mean "this task is done or on its way"


def init_ee():
    import ee
    ee.Initialize(project=os.getenv("GEE_PROJECT", C.GEE_PROJECT))
    return ee


def task_states(ee, prefix):
    """{description: state} of the tasks whose description starts with prefix, newest first wins."""
    out = {}
    for t in ee.data.getTaskList():
        d = t.get("description", "")
        if d.startswith(prefix) and d not in out:
            out[d] = t.get("state")
    return out


def print_status(prefix):
    ee = init_ee()
    tasks = task_states(ee, prefix)
    if not tasks:
        print(f"no {prefix}* tasks in the project")
    for desc, state in sorted(tasks.items()):
        print(f"{state:<10} {desc}")


def export_grouped_area(ee, code, desc, crs, crs_transform):
    """Hectares per value of the one-band integer image `code`, over C.GRID_BBOX on the given grid,
    as CSV (code, sum) to the Drive folder C.DRIVE_FOLDER. Returns the started task."""
    box = ee.Geometry.Rectangle(C.GRID_BBOX, None, False)
    groups = ee.List(ee.Image.pixelArea().divide(1e4).addBands(code).reduceRegion(
        reducer=ee.Reducer.sum().group(groupField=1, groupName="code"), geometry=box,
        crs=crs, crsTransform=crs_transform, maxPixels=1e13).get("groups"))
    fc = ee.FeatureCollection(groups.map(lambda g: ee.Feature(None, ee.Dictionary(g))))
    task = ee.batch.Export.table.toDrive(
        collection=fc, description=desc, folder=C.DRIVE_FOLDER, fileNamePrefix=desc,
        fileFormat="CSV", selectors=["code", "sum"])
    task.start()
    return task


def fetch_csvs(names, out_dir):
    """Download each Drive file in `names` (the newest one of that name) into out_dir."""
    import ee
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload

    # The earthengine credentials carry the Drive scope. No quota project, as in the fire team's
    # burnable_export.py --fetch: the call is billed to the OAuth client and needs no API enabled.
    stored = json.loads(Path("~/.config/earthengine/credentials").expanduser().read_text())
    creds = Credentials(None, refresh_token=stored["refresh_token"], token_uri=ee.oauth.TOKEN_URI,
                        client_id=stored.get("client_id", ee.oauth.CLIENT_ID),
                        client_secret=stored.get("client_secret", ee.oauth.CLIENT_SECRET),
                        scopes=stored.get("scopes", ee.oauth.SCOPES))
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        files = drive.files().list(q=f"name = '{name}' and trashed = false", orderBy="modifiedTime desc",
                                   fields="files(id,size,modifiedTime)").execute().get("files", [])
        if not files:
            print(f"missing {name} in Drive (check --status)")
            continue
        f = files[0]
        with open(out_dir / name, "wb") as out:
            dl = MediaIoBaseDownload(out, drive.files().get_media(fileId=f["id"]))
            done = False
            while not done:
                done = dl.next_chunk()[1]
        print(f"fetched {name}  {int(f['size']) / 1e6:.1f} MB  modified {f['modifiedTime']}"
              + (f"  ({len(files)} files with this name, took the newest)" if len(files) > 1 else ""))
