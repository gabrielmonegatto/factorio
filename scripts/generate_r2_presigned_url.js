import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";

const r2Client = new S3Client({
  endpoint: "https://dca6b1af1352f500d6eabe544b9222a3.r2.cloudflarestorage.com",
  region: "auto",
  credentials: {
    accessKeyId: "6aa1ac9af90fa274093da7c3cf782ffd",
    secretAccessKey: "320b3cc072f95c4362cc588d45697e2bc38ca7a7cb316aed43d3c173152b2f7a"
  }
});

async function main() {
  const command = new PutObjectCommand({
    Bucket: "channels",
    Key: "teable_local_backup_slim.dump"
  });

  try {
    // Generate pre-signed URL valid for 2 hours (7200 seconds)
    const url = await getSignedUrl(r2Client, command, { expiresIn: 7200 });
    console.log("🔗 URL_START");
    console.log(url);
    console.log("🔗 URL_END");
  } catch (err) {
    console.error("❌ Failed to generate pre-signed URL:", err);
  }
}

main();
