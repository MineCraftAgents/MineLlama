async function fillBucketWithWater(bot) {
  //地表に移動する
  await moveToGroundLevel(bot);
  
  // 周囲に地表の水源を探す
  let waterBlock = null;
  while (!waterBlock) {
      waterBlock = findSurfaceWaterBlock(bot);
      bot.chat("No surface water found nearby.");
      // return;
      await moveForward(bot, 64);
  }

  // Equip the bucket
  const bucket = bot.inventory.findInventoryItem(mcData.itemsByName.bucket.id);
  if (!bucket) {
    bot.chat("you don't have a bucket");
    return;
  }
  await bot.equip(bucket, "hand");

  await bot.pathfinder.goto(
    new GoalGetToBlock(waterBlock.position.x, waterBlock.position.y, waterBlock.position.z)
  );
  
  try {
    await bot.lookAt(waterBlock.position);
  } catch (error) {
    bot.chat(`bot.lookAtでエラー: ${error.message}`)
  }
    // Activate the bucket to collect water
  try {
    await bot.activateItem();
  } catch (error) {
    bot.chat(`bot.activateItemでエラー: ${error.message}`)
  }
  bot.chat("Filled the bucket with water.");
  
}
