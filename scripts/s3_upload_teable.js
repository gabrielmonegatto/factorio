import { S3Client, CreateBucketCommand } from "@aws-sdk/client-s3";
import { Upload } from "@aws-sdk/lib-storage";
import fs from "fs";

const s3Client = new S3Client({
  endpoint: "http://187.127.44.153:9000",
  region: "us-east-1",
  credentials: {
    accessKeyId: "minioadmin",
    secretAccessKey: "minioadmin_secret_pass"
  },
  forcePathStyle: true,
  requestHandlerOptions: {
    connectionTimeout: 60000,
    socketTimeout: 60000
  }
});

const localFile = 'C:\\Users\\Monegatto\\.gemini\\antigravity-ide\\brain\\16dc9239-ee35-40b1-b4b3-d9079f5f0732\\scratch\\teable_local_backup.dump';
const bucketName = "outline-holding";

async function main() {
  const fileStream = fs.createReadStream(localFile);
  const stats = fs.statSync(localFile);
  const totalSize = stats.size;
  
  console.log(`🚀 Ensuring S3 bucket "${bucketName}" exists...`);
  try {
    await s3Client.send(new CreateBucketCommand({ Bucket: bucketName }));
    console.log(`✅ Bucket "${bucketName}" ensured.`);
  } catch (err) {
    if (err.name === "BucketAlreadyExists" || err.name === "BucketAlreadyOwnedByYou" || err.code === "BucketAlreadyExists") {
      console.log(`ℹ️ Bucket "${bucketName}" already exists.`);
    } else {
      console.warn(`⚠️ Failed to create bucket: ${err.message}`);
    }
  }

  console.log(`🚀 Starting S3 Multipart Upload of ${(totalSize / (1024 * 1024)).toFixed(2)} MB to MinIO...`);
  
  try {
    const upload = new Upload({
      client: s3Client,
      params: {
        Bucket: bucketName,
        Key: "teable_local_backup.dump",
        Body: fileStream
      },
      queueSize: 3, // 3 parallel parts (safe and fast)
      partSize: 10 * 1024 * 1024 // 10MB parts
    });

    let lastProgressTime = Date.now();
    let lastLoaded = 0;

    upload.on("httpUploadProgress", (progress) => {
      const pct = ((progress.loaded / totalSize) * 100).toFixed(1);
      const now = Date.now();
      const timeDiff = (now - lastProgressTime) / 1000;
      
      // Log progress every 10MB uploaded or every 10 seconds
      if (progress.loaded - lastLoaded >= 10 * 1024 * 1024 || timeDiff >= 10) {
        const speed = timeDiff > 0 ? ((progress.loaded - lastLoaded) / (1024 * 1024) / timeDiff).toFixed(2) : 0;
        console.log(`Progress: ${pct}% | ${(progress.loaded / (1024 * 1024)).toFixed(1)} MB / ${(totalSize / (1024 * 1024)).toFixed(1)} MB | Speed: ${speed} MB/s`);
        lastProgressTime = now;
        lastLoaded = progress.loaded;
      }
    });

    await upload.done();
    console.log("✅ Upload Completed successfully via S3!");
  } catch (err) {
    console.error("❌ S3 Upload failed:", err);
  }
}

main();
