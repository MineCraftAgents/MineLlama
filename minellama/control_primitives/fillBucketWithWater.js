async function fillBucketWithWater(bot) {
  // Find a water block nearby
  const waterBlock = bot.findBlock({
    matching: mcData.blocksByName.water.id,
    maxDistance: 32
  });

  if (waterBlock) {
    bot.chat("Found water block")
  } else {
    bot.chat("No water block found nearby. Exploring...");
    waterBlock = await exploreUntil(bot, new Vec3(1, 0, 1), 60, () => {
      return bot.findBlock({
        matching: mcData.blocksByName.water.id,
        maxDistance: 32
      });
    });
    if (!waterBlock) {
      bot.chat("Still couldn't find any water block.");
      return; // 水が見つからなければ終了
    }
  }
  
  // Go to the water block
  await bot.pathfinder.goto(
    new GoalGetToBlock(waterBlock.position.x, waterBlock.position.y, waterBlock.position.z)
  );

  // Equip the bucket
  const bucket = bot.inventory.findInventoryItem(mcData.itemsByName.bucket.id);
  if (!bucket) {
    bot.chat("you don't have a bucket");
    return;
  }
  await bot.equip(bucket, "hand");

  // Look at the water block
  await bot.lookAt(waterBlock.position);
    // Activate the bucket to collect water
  await bot.activateItem();
  const water_bucket = bot.inventory.findInventoryItem(mcData.itemsByName.water_bucket.id);
  if (water_bucket) {
    bot.chat("Filled the bucket with water.");
  } else {
    bot.chat("Failed to fill the bucket with water.")
  }
}