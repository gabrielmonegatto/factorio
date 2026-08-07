import { S3Client, ListBucketsCommand, CreateBucketCommand } from "@aws-sdk/client-s3";

const r2Client = new S3Client({
  endpoint: "https://dca6b1af1352f500d6eabe544b9222a3.r2.cloudflarestorage.com",
  region: "auto",
  credentials: {
    accessKeyId: "6aa1ac9af90fa274093da7c3cf782ffd",
    secretAccessKey: "320b3cc072f95c4362cc588d45697e2bc38ca7a7cb316aed43d3c173152b2f7a"
  }
});

async function main() {
  console.log("🔍 1. Listing all buckets in Cloudflare R2...");
  try {
    const listRes = await r2Client.send(new ListBucketsCommand({}));
    console.log("Current Buckets:", listRes.Buckets || []);
  } catch (err) {
    console.error("❌ Failed to list R2 buckets:", err.message);
  }

  const targetBucket = "channels";
  console.log(`\n🆕 2. Ensuring bucket "${targetBucket}" exists in R2...`);
  try {
    await r2Client.send(new CreateBucketCommand({ Bucket: targetBucket }));
    console.log(`✅ Bucket "${targetBucket}" created/ensured successfully in Cloudflare R2!`);
  } catch (err) {
    if (err.name === "BucketAlreadyExists" || err.name === "BucketAlreadyOwnedByYou" || err.code === "BucketAlreadyExists") {
      console.log(`ℹ️ Bucket "${targetBucket}" already exists and is owned by you.`);
    } else {
      console.error(`❌ Failed to create bucket "${targetBucket}":`, err.message);
    }
  }
}

main();
