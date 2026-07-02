import os
import subprocess
import json
import boto3
import runpod
from botocore.config import Config

R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY")
R2_ENDPOINT = os.environ.get("R2_ENDPOINT")
R2_PUBLIC_URL = os.environ.get("R2_PUBLIC_URL")
BUCKET_NAME = "mananciall"

# Initialize boto3 client
s3 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4"),
    region_name="auto"
)

def handler(job):
    job_input = job.get('input', {})
    
    # 1. Prepare properties
    composition = job_input.get('composition', 'BibleNarration')
    props = job_input.get('props', {})
    
    # Save props to temporary JSON file
    props_path = "/tmp/props.json"
    with open(props_path, "w", encoding="utf-8") as f:
        json.dump(props, f, ensure_ascii=False)
        
    output_path = f"/tmp/{job['id']}.mp4"
    
    # 2. Run Remotion render
    print(f"🎬 Running remotion render for composition '{composition}'...")
    cmd = [
        "npx", "remotion", "render",
        composition,
        output_path,
        f"--props={props_path}"
    ]
    
    try:
        # Run command and capture output
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("Stdout:", res.stdout)
    except subprocess.CalledProcessError as err:
        print("Error during render:")
        print("Stdout:", err.stdout)
        print("Stderr:", err.stderr)
        raise Exception(f"Remotion render failed: {err.stderr or err.stdout}")
        
    if not os.path.exists(output_path):
        raise FileNotFoundError("Render finished but output file was not found.")
        
    # 3. Upload output to R2
    r2_key = f"renders/{job['id']}.mp4"
    print(f"📤 Uploading rendered video to R2 under key: '{r2_key}'...")
    
    s3.upload_file(
        Filename=output_path,
        Bucket=BUCKET_NAME,
        Key=r2_key,
        ExtraArgs={"ContentType": "video/mp4"}
    )
    
    # Clean up temp files
    if os.path.exists(props_path):
        os.remove(props_path)
    if os.path.exists(output_path):
        os.remove(output_path)
        
    # 4. Return the public URL
    public_url = f"{R2_PUBLIC_URL.rstrip('/')}/{r2_key}"
    print(f"✅ Render and upload completed successfully! URL: {public_url}")
    return {"videoUrl": public_url}

runpod.serverless.start({"handler": handler})
