import { S3Client, GetObjectCommand } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";
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

const localFile = 'C:\\Users\\Monegatto\\.gemini\\antigravity-ide\\brain\\16dc9239-ee35-40b1-b4b3-d9079f5f0732\\scratch\\teable_local_content_tables.dump';
const bucketName = "channels";
const key = "teable_local_content_tables.dump";

async function main() {
  const fileStream = fs.createReadStream(localFile);
  
  console.log(`🚀 Uploading ${localFile} to Cloudflare R2 bucket "${bucketName}"...`);
  try {
    const upload = new Upload({
      client: r2Client,
      params: {
        Bucket: bucketName,
        Key: key,
        Body: fileStream
      }
    });

    await upload.done();
    console.log("✅ Upload completed successfully to R2.");

    // Generate GET presigned URL
    const getCommand = new GetObjectCommand({ Bucket: bucketName, Key: key });
    const downloadUrl = await getSignedUrl(r2Client, getCommand, { expiresIn: 3600 });
    
    console.log("\n🔗 DOWNLOAD_URL_START");
    console.log(downloadUrl);
    console.log("🔗 DOWNLOAD_URL_END");

  } catch (err) {
    console.error("❌ Failed:", err);
  }
}

main();
