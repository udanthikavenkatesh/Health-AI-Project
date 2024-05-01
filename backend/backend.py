from typing import Union
from heartrate import getHR
from fastapi import FastAPI, Request, Response
from starlette.responses import JSONResponse
import base64
import time

app = FastAPI()


@app.post("/gethr")
async def gethr(request:Request):
    start = time.time()
    print("Downloading...")
    # {"userid":"str","ext":"mp4","data":"base64"}
    data = await request.json()
    userid = data.get("userid")
    ext = data.get("ext")
    base64_data = data.get("data")

    if not (userid and ext and base64_data):
        return JSONResponse({"error": "Incomplete data provided"}, status_code=400)

    try:
        # Decode base64 data
        binary_data = base64.b64decode(base64_data)

        # Save binary data to a temporary file
        filename = f"{userid}.{ext}"
        with open(filename, "wb") as file:
            file.write(binary_data)

        # Return a response confirming successful storage
        end = time.time()
        print("Download time (s) : ", end-start)
        start = time.time()
        v = getHR(filename)
        end = time.time()
        print("Processing time (s) :", end-start)
        print(v)
        with open("x.json","w") as f:
            import json
            json.dump(v,f)
        res = JSONResponse(v)
        #return JSONResponse({"message": f"File {filename} stored successfully"}, status_code=200)
        return res
    
    except Exception as e:
        return JSONResponse({"error": f"Failed to store file: {str(e)}"}, status_code=500)
