async function fillBucketWithWater(bot) {
  //地表に移動する
  await moveToGroundLevel(bot);
  
  // Find a water block nearby
      // 周囲に地表の水源を探す
  let waterBlock = null;
  while (!waterBlock) {
      waterBlock = findSurfaceWaterBlock(bot);
      bot.chat("No surface water found nearby.");
      // return;
      await moveForward(bot, 64);
  }
  
  bot.chat("Water source found. Heading to the water source.");
  
  // 水源の5マス以内に入るまで移動
  await bot.pathfinder.goto(new GoalNear(waterBlock.position.x, waterBlock.position.y, waterBlock.position.z, waterProximityRadius));
  bot.chat("Arrived near the water source.");

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
    bot.chat("Failed to fill the bucket with water.");
  }
}