import { S3Client } from "@aws-sdk/client-s3";
import { Upload } from "@aws-sdk/lib-storage";
import fs from "fs";

const r2Client = new S3Client({
  endpoint: "https://dca6b1af1352f500d6eabe544b9222a3.r2.cloudflarestorage.com",
  region: "auto",
  credentials: {
    accessKeyId: "6aa1ac9af90fa274093da7c3cf782ffd",
    secretAccessKey: "320b3cc072f95c4362cc588d45697e2bc38ca7a7cb316aed43d3c173152b2f7a"
  }
});

const localFile = 'C:\\Users\\Monegatto\\.gemini\\antigravity-ide\\brain\\16dc9239-ee35-40b1-b4b3-d9079f5f0732\\scratch\\teable_local_backup_slim.dump';
const bucketName = "channels";

async function main() {
  const fileStream = fs.createReadStream(localFile);
  const stats = fs.statSync(localFile);
  const totalSize = stats.size;
  
  console.log(`🚀 Starting S3 Multipart Upload of ${(totalSize / (1024 * 1024)).toFixed(2)} MB to Cloudflare R2...`);
  
  try {
    const upload = new Upload({
      client: r2Client,
      params: {
        Bucket: bucketName,
        Key: "teable_local_backup_slim.dump",
        Body: fileStream
      },
      queueSize: 4, // Concurrency
      partSize: 15 * 1024 * 1024 // 15MB chunks
    });

    let lastLoggedPct = 0;
    upload.on("httpUploadProgress", (progress) => {
      const pct = Math.round((progress.loaded / totalSize) * 100);
      if (pct >= lastLoggedPct + 5) {
        lastLoggedPct = pct;
        console.log(`Progress: ${pct}% (${(progress.loaded / (1024 * 1024)).toFixed(2)} MB / ${(totalSize / (1024 * 1024)).toFixed(2)} MB)`);
      }
    });

    await upload.done();
    console.log("✅ Upload Completed successfully via Cloudflare R2!");
  } catch (err) {
    console.error("❌ R2 Upload failed:", err);
  }
}

main();
